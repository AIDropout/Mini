import uuid
from datetime import timedelta
from typing import Dict, List, Optional, Tuple
import random

from fastapi import HTTPException, BackgroundTasks

from config.config import config
from mini.core.enums import MessageTaskType, MessagingProviderType
from mini.core.exceptions import RoomDisabledByAdminError
from mini.core.models.context import Context
from mini.core.models.message import MiniMessage
from mini.core.models.message_tasks import ProactiveTask, ResponseTask
from mini.database.database import DatabaseManager
from mini.database.models import Agent, Message, Room, Tables, User
from mini.database.tables.user_service import UserTableService
from mini.database.tables.message_service import MessageTableService
from mini.messaging.factory import MessageTaskFactory
from mini.messaging.providers import MessagingProvider, messaging_providers
from mini.messaging.providers.bird import BirdMessaging
from mini.messaging.providers.discord import discord_manager
from mini.messaging.providers.instagram import InstagramMessaging
from mini.utils.time import TimeManager


class MessagingService:
    """Central service that handles message storage"""

    def __init__(
        self,
        database_manager: DatabaseManager,
        user_table_service: UserTableService,
        system_time_manager: TimeManager,
        message_table_service: MessageTableService,
        message_task_factory: MessageTaskFactory,
    ) -> None:
        self.database_manager = database_manager
        self.user_table_service = user_table_service
        self.system_time_manager = system_time_manager
        self.message_table_service = message_table_service
        self.message_task_factory = message_task_factory

    def handle_incoming_message(
        self, provider_name: MessagingProviderType, request_body: dict, background_tasks: BackgroundTasks
    ) -> None:
        """
        Function called by our webhooks (e.g. Bird and Instagram)

        - Inserts message
        - Handles special cases
        - Calculates human-like response delay
        - Schedules response
        """
        messaging_provider = messaging_providers.get(provider_name)
        message = messaging_provider.receive_message(request_body)
        context = self.message_task_factory._get_context_from_message(message)

        # Handle special cases:
        if context.room.disabled_by_admin:
            raise RoomDisabledByAdminError(room_id=context.room.id)
        if message.content == "STOP":  # TODO: handle other keywords
            # TODO: cancel all scheduled jobs / make room disabled
            return
        if config.ENVIRONMENT == "production":
            discord_manager.log_message(
                message=f"-# {context.user.phone_number} -> {context.agent.name}: {message.content}"
            )
        if message.content == config.SECRET_PHRASES.reset_user:
            self.database_manager.supabase.auth.admin.delete_user(context.user.id)
            self.user_table_service.delete_user(context.user.id)
            messaging_provider.send_message(
                text="Successfully deleted your user from Auth tables and Users table"
            )
            return

        # Insert message
        self.message_table_service.add_message(
            context.room.id, context.user.id, message.content
        )

        # Update rooms table
        time_stamp = self.system_time_manager.get_user_timestamp()
        self.database_manager.update(
            Tables.ROOMS,
            {Tables.ROOMS__last_msg_sent_at: time_stamp},
            condition_key=Tables.ROOMS__id,
            condition_value=context.room.id,
        )

        # Simulate human-like response time
        delay = random.randint(3, 20)

        from mini.messaging.send_message.send_message import send_message

        send_message.apply_async(
            kwargs={
                "provider_name": provider_name.value,
                "room_id": context.room.id,
                "type": MessageTaskType.RESPONSE.value,
            },
            countdown=delay,
        )
