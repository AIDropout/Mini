import random

from config.config import config
from mini.controller.task.task_scheduler import SchedulerService
from mini.core.logger import get_logger
from mini.core.schema.tables import Message, Tables
from mini.manager.database import DatabaseManager
from mini.manager.messaging import MessagingManagerFactory, discord_manager
from mini.service.base import Service
from mini.service.context_factory import ContextFactory
from mini.utils.utils import log_error_to_discord

logger = get_logger(__name__)


class ReplyService(Service):
    def __init__(
        self,
        database_manager: DatabaseManager,
        messaging_manager_factory: MessagingManagerFactory,
        context_factory: ContextFactory,
        scheduler_service: SchedulerService,
    ):
        super().__init__(database_manager)
        self.messaging_manager_factory = messaging_manager_factory
        self.context_factory = context_factory
        self.scheduler_service = scheduler_service

    def handle_respond(self, request_body: dict) -> None:
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
                discord_manager.send_message_to_channel(
                    message=f"-# {context.user.phone_number} -> {context.agent.name}: {message.content}",
                    channel="https://discord.com/api/webhooks/1285123477619081237/xCmCDv_j0XV7Sm0xSAfbLxM603AaJML9TJVefhmiDkglfAmYwh9ElqYQgo88qHk1Ubz1",
                )

            # Calculate delay and schedule response
            self.scheduler_service.schedule_respond(
                delay=0,
                message=message,
                context=context,
            )
        except Exception as e:
            msg = log_error_to_discord("room_id", context.room.id)
            logger.exception(msg)
