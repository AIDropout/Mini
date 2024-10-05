import random
from mini.server.celery import celery_app as app
from fastapi import BackgroundTasks

from config.config import config
from mini.core.enums import MessageTaskType, MessagingProviderType
from mini.core.logger import get_logger
from mini.core.models.context import Context
from mini.core.models.message import MiniMessage
from mini.database.database import DatabaseManager
from mini.database.tables.user_service import UserTableService
from mini.database.tables.room_service import RoomTableService
from mini.database.tables.message_service import MessageTableService
from mini.database.tables.session_service import SessionTableService
from mini.messaging.factory import MessageTaskFactory
from mini.messaging.providers import messaging_providers
from mini.messaging.providers.discord import discord_manager
from mini.server.redis.cancellable import CancellableTask

logger = get_logger(__name__)


class MessagingService:
    """Central service that handles message storage and calls a celery task"""

    def __init__(
        self,
        database_manager: DatabaseManager,
        user_table_service: UserTableService,
        room_table_service: RoomTableService,
        session_table_service: SessionTableService,
        message_table_service: MessageTableService,
        message_task_factory: MessageTaskFactory,
    ) -> None:
        self.database_manager = database_manager
        self.user_table_service = user_table_service
        self.room_table_service = room_table_service
        self.session_table_service = session_table_service
        self.message_table_service = message_table_service
        self.message_task_factory = message_task_factory
        self.messaging_provider = None

    def handle_incoming_message(
        self,
        provider_name: MessagingProviderType,
        request_body: dict,
        background_tasks: BackgroundTasks,
    ) -> None:
        """
        Function called by our webhooks (e.g. Bird and Instagram)

        - Handles special cases
        - Inserts message
        - Calculates human-like response delay
        - Schedules response
        """
        self.messaging_provider = messaging_providers.get(provider_name)
        message = self.messaging_provider.receive_message(request_body)
        context = self.message_task_factory._get_context_from_message(message)
        if not self._handle_special_cases(context, message):
            return

        # Update rooms, messages, & session table
        message = self.message_table_service.add_message(
            context.room.id,
            context.user.id,
            message.content,
            session_id=context.session.id,
        )

        # Make updates to tables
        self.room_table_service.update_room_last_sent(context.room.id)
        self.session_table_service.update_active_session(context.session)

        # Simulate human-like response time
        delay = (
            self._generate_response_delay()
            if config.DEV_CONFIG.enable_response_delay
            else 0
        )
        logger.info("-----")
        logger.info(delay)

        # Celery task
        from mini.server.celery.tasks.send_message import send_message

        logger.info(app.tasks)
        task = send_message.apply_async(
            kwargs={
                "provider_name": provider_name.value,
                "room_id": context.room.id,
                "type": MessageTaskType.RESPONSE.value,
            },
            countdown=delay,
        )

        # Store task id to redis (room:message_id)
        logger.info(f"🩷🩷 adding task {task.id}")
        CancellableTask.register_task(context.room.id, task.id)

    def _handle_special_cases(self, context: Context, message: MiniMessage) -> bool:
        """
        Handle special cases. Return boolean whether to continue processing.
        """
        if context.room.disabled_by_admin:
            return False
        if message.content in ["STOP", "STOPALL"]:
            # TODO: cancel all scheduled jobs / make room disabled
            return False
        if config.ENVIRONMENT == "production":
            discord_manager.log_message(
                message=f"-# {context.user.phone_number} -> {context.agent.name}: {message.content}"
            )
        if message.content == config.SECRET_PHRASES.reset_user:
            self.database_manager.supabase.auth.admin.delete_user(context.user.id)
            self.user_table_service.delete_user(context.user.id)
            self.messaging_provider.send_message(
                text="Successfully deleted your user from Auth tables and Users table"
            )
            return False
        return True

    def _generate_response_delay(self) -> int:
        """
        Returns delay in seconds
        """
        # TODO: eventually make it based on how many messages there are in the session -> more messages = longer delay
        return random.randint(10, 60)
