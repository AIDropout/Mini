import random

from config.config import config
from mini.controller.task.task_scheduler import SchedulerService
from mini.core.logger import get_logger
from mini.core.schema.tables import Message, Tables
from mini.manager.database import DatabaseManager
from mini.manager.messaging import MessagingManagerFactory
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

            # Calculate delay and schedule response
            delay = self._calculate_response_delay(room_id=context.room.id)
            self.scheduler_service.schedule_respond(
                delay=delay,
                message=message,
                context=context,
            )
        except Exception as e:
            msg = log_error_to_discord("room_id", context.room.id)
            logger.exception(msg)

    def _calculate_response_delay(self, room_id: int) -> int:
        """
        Calculate a human-like delay in seconds for message responses.

        :param messages: List of message objects, sorted by creation time (newest first)
        :return: Delay in seconds
        """

        recent_messages = self.database_manager.get_multiple_rows(
            Tables.MESSAGES,
            max_rows=5,
            order_by=Tables.MESSAGES__created_at,
            order_desc=True,
            conditions={Tables.MESSAGES__room_id: room_id},
        )

        if not recent_messages:
            return random.randint(5, 15)  # Default delay if no messages

        return 1  # temp

        # for debugging
        logger.info("___")
        logger.info(config.ENABLE_RESPONSE_DELAY)
        if not config.ENABLE_RESPONSE_DELAY:
            return 1
