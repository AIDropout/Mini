from fastapi import BackgroundTasks
import random

from config.config import config
from mini.core.logger import get_logger
from mini.core.schema.tables import Message, Tables
from mini.storage.database import DatabaseManager
from mini.manager.messaging import MessagingManagerFactory, discord_manager
from mini.service.base import Service
from mini.service.context_factory import ContextFactory
from datetime import datetime, timedelta
from uuid import uuid4

from mini.controller.agent_controller import run_agent
from mini.controller.task import RespondTask, TaskType
from mini.server.cancel import CancelManager
from mini.server.redis import RedisManager
from mini.service.base import Service

logger = get_logger(__name__)


class ReplyService(Service):
    def __init__(
        self,
        database_manager: DatabaseManager,
        messaging_manager_factory: MessagingManagerFactory,
        context_factory: ContextFactory,
        cancel_manager: CancelManager,
        redis_manager: RedisManager,
    ):
        super().__init__(database_manager)
        self.messaging_manager_factory = messaging_manager_factory
        self.context_factory = context_factory
        self.cancel_manager = cancel_manager
        self.redis_manager = redis_manager

    def handle_respond(
        self, request_body: dict, background_tasks: BackgroundTasks
    ) -> None:
        context = None
        try:
            # Process request
            messaging_manager = self.messaging_manager_factory.get_manager_from_request(
                request_body
            )
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

            # Insert user message
            self.database_manager.insert(
                Tables.MESSAGES,
                Message(
                    room_id=context.room.id,
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

            # Delay is set to 0. In the future we could implement esponse rate limiting / human responsive times.
            delay = 0
            scheduled_time = datetime.now() + timedelta(seconds=delay)
            room_id = context.room.id

            task = RespondTask(
                id=str(uuid4()),
                scheduled_for=scheduled_time,
                user_message=message,
                context=context,
            )

            # Cancel this task if a new task has come in
            if self.cancel_manager.newer_task_found(room_id, task.id):
                return

            # Store task data in Redis
            self.redis_manager.set(
                key=f"{room_id}:{task.id}",
                value=task.model_dump_json(),
                expiry=delay + 120,
            )

            # Run agent in the background using a Celery worker
            new_task = run_agent.apply_async(
                args=[room_id, task.id, TaskType.RESPOND], countdown=delay
            )

            if new_task:
                logger.info(
                    f"🟢 Scheduled short-term task in {delay} seconds\n"
                    f"🟢 Current time: {datetime.now().isoformat()}\n"
                    f"🟢 Scheduled response time: {task.scheduled_for.isoformat()}"
                )

        except Exception as e:
            msg = discord_manager.log_error(f"room_id={context.room.id}")
            logger.exception(msg)
