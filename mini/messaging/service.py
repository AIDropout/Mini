"""Core Messaging Service file that runs the core response logic."""

from datetime import datetime, timedelta
from typing import Dict, Optional
from uuid import uuid4

from fastapi import BackgroundTasks

from config.config import config
from mini.agent.run_agent import run_agent
from mini.agent.tasks.models import MessageTask
from mini.core.logger import get_logger
from mini.database.database import DatabaseManager
from mini.database.models import Message, Tables
from mini.messaging.base import MessagingProvider
from mini.messaging.bird.bird import BirdMessagingService
from mini.messaging.context import Context, ContextFactory
from mini.messaging.discord.discord import discord_manager
from mini.messaging.instagram.instagram import InstagramMessagingService
from mini.messaging.models import MessagingProviderEnum, MiniMessage, ResponseTypeEnum
from mini.server.cancel import CancelManager
from mini.server.redis import RedisManager

logger = get_logger(__name__)


class MessagingService:
    def __init__(
        self,
        database_manager: DatabaseManager,
        context_factory: ContextFactory,
        cancel_manager: CancelManager,
        redis_manager: RedisManager,
        bird_manager: BirdMessagingService,
        instagram_manager: InstagramMessagingService,
    ):
        self.database_manager = database_manager
        self.context_factory = context_factory
        self.cancel_manager = cancel_manager
        self.redis_manager = redis_manager
        self.providers: Dict[MessagingProviderEnum, MessagingProvider] = {
            MessagingProviderEnum.BIRD: bird_manager,
            MessagingProviderEnum.INSTAGRAM: instagram_manager,
        }

    def handle_incoming_message(
        self,
        provider: MessagingProviderEnum,
        request_body: dict,
        background_tasks: BackgroundTasks,
    ) -> None:
        context: Optional[Context] = None
        task: Optional[MessageTask] = None
        try:
            # Get correct provider class given provider name
            messaging_provider = self.providers.get(provider)
            if not messaging_provider:
                raise ValueError(f"Unsupported message provider: {provider}")

            # Use messaging provider to process request body and format message and context
            message, context = self._process_incoming_message(
                messaging_provider, request_body
            )

            if self._handle_reset_user(
                messaging_provider, message.content, context.user.id
            ):
                return
            task = self._create_task(message.id, provider, request_body)
            self._store_task_to_redis(context.room.id, task)
            if self.cancel_manager.newer_message_found(
                context.room.id, task.message_id
            ):
                return
            self._insert_and_log_user_message(message, context, background_tasks)
            delay = 0  # Future scheduling logic goes here
            new_task = run_agent.apply_async(
                args=[context.room.id, message.id], countdown=delay
            )
            if new_task:
                logger.info(
                    f"🟢 Scheduled short-term task in 0 seconds\n"
                    f"🟢 Current time: {datetime.now().isoformat()}\n"
                    f"🟢 Scheduled time: {task.scheduled_time}\n"
                )

        except Exception as e:
            self._handle_error(
                context.room.id if context else None, task.message_id if task else None
            )

    def _process_incoming_message(
        self, messaging_provider: MessagingProvider, request_body: dict
    ):
        message = messaging_provider.receive_message(request_body)
        context = self.context_factory.get_context_from_message(message)

        if context.room.disabled_by_admin:
            logger.warning(f"Room {context.room.id} disabled. Canceling process.")
            raise ValueError("Room disabled by admin")

        return message, context

    def _handle_reset_user(
        self,
        messaging_provider: MessagingProvider,
        message_content: str,
        user_id: str,
    ) -> bool:
        if message_content == config.SECRET_PHRASES.reset_user:
            self.database_manager.supabase.auth.admin.delete_user(user_id)
            self.database_manager.delete(Tables.USERS, {Tables.USERS__id: user_id})
            messaging_provider.send_message(
                text="Successfully deleted your user from Auth tables and Users table"
            )
            return True
        return False

    def _create_task(
        self,
        message_id: str,
        provider: MessagingProviderEnum,
        request_body: dict,
        response_type: ResponseTypeEnum = ResponseTypeEnum.RESPOND,
    ) -> MessageTask:
        delay = 0  # Implement delay logic here
        return MessageTask(
            message_id=message_id,
            response_type=response_type,
            created_at=datetime.now(),
            scheduled_time=datetime.now() + timedelta(seconds=delay),
            provider=provider,
            request_body=request_body,
        )

    def _store_task_to_redis(self, room_id: str, task: MessageTask):
        self.redis_manager.set(
            key=f"{room_id}:{task.message_id}",
            value=task.model_dump_json(),
            expiry=120,  # Assuming delay is 0
        )

    def _insert_and_log_user_message(
        self, message: MiniMessage, context: Context, background_tasks: BackgroundTasks
    ):
        self.database_manager.insert(
            Tables.MESSAGES,
            Message(
                room_id=context.room.id,
                sender_id=context.user.id,
                content=message.content,
            ),
        )

        if config.ENVIRONMENT == "production":
            background_tasks.add_task(
                discord_manager.log_message,
                message=f"-# {context.user.phone_number} -> {context.agent.name}: {message.content}",
            )

    def _handle_error(self, room_id: Optional[str], task_id: Optional[str]):
        if room_id and task_id:
            self.cancel_manager.remove_task(room_id, task_id)
        msg = discord_manager.log_error(f"room_id={room_id}")
        logger.exception(msg)
