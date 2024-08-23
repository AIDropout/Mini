import random
from typing import List
from zootopia.manager.database import DatabaseManager
from zootopia.manager.messaging import MessagingManagerFactory
from zootopia.core.schema.tables import Message, Tables
from zootopia.core.error import error_handler
from zootopia.controller.task.task_scheduler import SchedulerService
from zootopia.controller.task.task_types import RespondTask
from datetime import datetime, timezone
from zootopia.core.logger import get_logger
from zootopia.service.base import Service
from zootopia.service.context_factory import ContextFactory
from config.config import config
import os
from urllib.parse import urlparse

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
    def handle_respond(self, request_body: dict):
        print(request_body)
        messaging_manager = self.messaging_manager_factory.get_manager_from_request(
            request_body
        )
        message = messaging_manager.receive_message(request_body)

        context = self.context_factory.create_message_context(message)

        inserted_message = self.database_manager.insert(
            Tables.MESSAGES,
            Message(
                room_id=context.room.id,
                sender_id=context.user.id,
                content=message.content,
            ),
        )

        recent_messages = self.database_manager.get_multiple_rows(
            Tables.MESSAGES,
            max_rows=5,
            order_by=Tables.MESSAGES__created_at,
            order_desc=True,
            conditions={Tables.MESSAGES__room_id: context.room.id},
        )
        delay = self._calculate_response_delay(recent_messages)

        self.scheduler_service.schedule_respond(
            delay=delay,
            message=message,
            context=context,
        )

    def _calculate_response_delay(self, messages: List[Message]) -> int:
        """
        Calculate a human-like delay in seconds for message responses.

        :param messages: List of message objects, sorted by creation time (newest first)
        :return: Delay in seconds
        """
        if not messages:
            return random.randint(5, 15)  # Default delay if no messages

        try:
            last_message_time = datetime.fromisoformat(
                messages[0]["created_at"].replace("Z", "+00:00")
            ).replace(tzinfo=timezone.utc)
            time_since_last_message = (
                datetime.now(timezone.utc) - last_message_time
            ).total_seconds()
        except (ValueError, KeyError) as e:
            logger.error(f"Error parsing message time: {e}")
            return random.randint(
                5, 15
            )  # Default delay if there's an error parsing time

        # for debugging
        if not config.ENABLE_RESPONSE_DELAY:
            return 1

        # Determine delay based on time since last message
        if time_since_last_message < 60:  # Within a minute
            return random.randint(5, 30)
        elif time_since_last_message < 300:  # Within 5 minutes
            return random.randint(30, 180)
        elif time_since_last_message < 3600:  # Within an hour
            return random.randint(3 * 60, 20 * 60)  # 3 to 20 minutes
        elif time_since_last_message < 86400:  # Within a day
            return random.randint(30 * 60, 4 * 60 * 60)  # 30 minutes to 4 hours
        else:  # More than a day
            return random.randint(4 * 60 * 60, 24 * 60 * 60)  # 4 to 24 hours
