import random
from datetime import datetime, timezone
import traceback

from config.config import config
from mini.controller.task.task_scheduler import SchedulerService
from mini.controller.task.task_types import RespondTask
from mini.core.error import error_handler
from mini.core.logger import get_logger
from mini.core.schema.tables import Message, Tables
from mini.manager.database import DatabaseManager
from mini.manager.messaging import MessagingManagerFactory, discord_manager
from mini.service.base import Service
from mini.service.context_factory import ContextFactory
from mini.utils.utils import get_infostring

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

    @error_handler("ReplyService")
    def handle_respond(self, request_body: dict) -> None:
        try:
            # Process request
            messaging_manager = self.messaging_manager_factory.get_manager_from_request(
                request_body
            )
            message = messaging_manager.receive_message(request_body)

            context = self.context_factory.create_message_context(message)

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
                context=context.l,
            )
        except Exception as e:
            error_traceback = traceback.format_exc()
            msg = f"⚠️__**ERROR**__⚠️\n-# {get_infostring()} 🏷️ room_id={context.room.id}\n```{error_traceback}```"
            discord_manager.send_message_to_channel(msg, config.DISCORD_CONFIG.server_status_webhook_url)
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
