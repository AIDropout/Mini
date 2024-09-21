"""Core Messaging Service file that runs the core response logic."""

from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import BackgroundTasks

from config.config import config
from mini.agent.run_agent import run_agent
from mini.agent.tasks.models import RespondTask
from mini.core.logger import get_logger
from mini.database.models import Message, Tables
from mini.messaging.discord.discord import discord_manager
from mini.messaging.bird.bird import BirdManager
from mini.server.cancel import CancelManager
from mini.server.redis import RedisManager
from mini.messaging.context import ContextFactory
from mini.database.database import DatabaseManager

logger = get_logger(__name__)


class ReplyService:
    def __init__(
        self,
        database_manager: DatabaseManager,
        context_factory: ContextFactory,
        cancel_manager: CancelManager,
        redis_manager: RedisManager,
    ):
        self.database_manager = database_manager
        self.context_factory = context_factory
        self.cancel_manager = cancel_manager
        self.redis_manager = redis_manager
        self.room_id: str = None
        self.task_id: str = None

    def handle_respond(
        self, request_body: dict, background_tasks: BackgroundTasks
    ) -> None:
        context = None
        try:
            # Process request
            messaging_manager = BirdManager()
            message = messaging_manager.receive_message(request_body)

            context = self.context_factory.create_message_context(message)

            if context.room.disabled_by_admin:
                logger.warning(f"Room {context.room.id} disabled. Canceling process.")
                return

            # Reset admin user with secret passphrase
            if message.content == config.SECRET_PHRASES.reset_user:
                self.database_manager.supabase.auth.admin.delete_user(context.user.id)
                self.database_manager.delete(
                    Tables.USERS, {Tables.USERS__id: context.user.id}
                )
                messaging_manager.send_message(
                    text="Successfully deleted your user from Auth tables and Users table"
                )
                return

            # Delay is set to 0. In the future we could implement esponse rate limiting / human responsive times.
            delay = 0
            scheduled_time = datetime.now() + timedelta(seconds=delay)

            task = RespondTask(
                id=str(uuid4()),
                scheduled_for=scheduled_time,
                user_message=message,
                context=context,
                created_at=datetime.now().isoformat(),
            )
            self.room_id = context.room.id
            self.task_id = task.id

            # Cancel this task if a new task has come in
            if self.cancel_manager.newer_task_found(self.room_id, self.task_id):
                return

            # Store task data in Redis
            self.redis_manager.set(
                key=f"{self.room_id}:{self.task_id}",
                value=task.model_dump_json(),
                expiry=delay + 120,
            )

            # Insert user message
            self.database_manager.insert(
                Tables.MESSAGES,
                Message(
                    room_id=self.room_id,
                    sender_id=context.user.id,
                    content=message.content,
                ),
            )

            # Log user message to discord
            if config.ENVIRONMENT == "production":
                background_tasks.add_task(
                    discord_manager.log_message,
                    message=f"-# {context.user.phone_number} -> {context.agent.name}: {message.content}",
                )

            # Run agent in the background using a Celery worker
            new_task = run_agent.apply_async(args=[self.room_id, self.task_id], countdown=delay)

            if new_task:
                logger.info(
                    f"🟢 Scheduled short-term task in {delay} seconds\n"
                    f"🟢 Current time: {datetime.now().isoformat()}\n"
                    f"🟢 Scheduled response time: {task.scheduled_for.isoformat()}"
                )

        except Exception as e:
            self.cancel_manager.remove_task(self.room_id, self.task_id)
            msg = discord_manager.log_error(f"room_id={self.room_id}")
            logger.exception(msg)
