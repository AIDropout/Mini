import uuid
from typing import Optional, Tuple, List, Dict

from fastapi import HTTPException

from config.config import config
from mini.core.exceptions import RoomDisabledByAdminError
from mini.core.models.context import Context
from mini.core.models.message import MessagingProviderType, MiniMessage
from mini.core.models.message_tasks import ProactiveTask, ResponseTask, MessageTaskType
from mini.database.database import DatabaseManager
from mini.messaging.providers.discord import discord_manager
from mini.database.models import Agent, Room, Tables, User, Message
from mini.database.tables.user_service import UserTableService
from mini.messaging.providers import MessagingProvider, messaging_providers
from mini.messaging.providers.bird import BirdMessaging
from mini.messaging.providers.instagram import InstagramMessaging


class MessagingService:
    """Central service that handles message storage and message task creation"""

    def __init__(
        self, database_manager: DatabaseManager, user_table_service: UserTableService
    ) -> None:
        self.database_manager = database_manager
        self.user_table_service = user_table_service

    def process_and_store_incoming_message(
        self, provider_name: MessagingProviderType, request_body: dict
    ):
        """Used in response route"""
        messaging_provider = messaging_providers.get(provider_name)
        if not messaging_provider:
            raise ValueError(f"Unsupported message provider: {provider_name}")
        message = messaging_provider.receive_message(request_body)
        context = self._get_context_from_message(message)

        if context.room.disabled_by_admin:
            raise RoomDisabledByAdminError(room_id=context.room.id)

        if message.content == config.SECRET_PHRASES.reset_user:
            self.database_manager.supabase.auth.admin.delete_user(context.user.id)
            self.database_manager.delete(
                Tables.USERS, {Tables.USERS__id: context.user.id}
            )
            messaging_provider.send_message(
                text="Successfully deleted your user from Auth tables and Users table"
            )
            return

        self.database_manager.insert(
            Tables.MESSAGES,
            Message(
                room_id=context.room.id,
                sender_id=context.user.id,
                content=message.content,
            ),
        )
        if config.ENVIRONMENT == "production":
            discord_manager.log_message(
                message=f"-# {context.user.phone_number} -> {context.agent.name}: {message.content}"
            )
        return context.room.id

    def _get_recent_messages(
        self, context: Context, count: int = 20
    ) -> List[Dict[str, str]]:
        """
        Get the most recent messages for a given room ID.

        Args:
        - count (int): The number of recent messages to fetch. Defaults to 10.

        Returns:
        - List[Dict[str, str]]: A list of dictionaries with 'role' and 'content' keys.
        """
        messages = self.database_manager.get_multiple_rows(
            table_name=Tables.MESSAGES,
            max_rows=count,
            order_by=Tables.MESSAGES__created_at,
            order_desc=True,
            conditions={Tables.MESSAGES__room_id: context.room.id},
        )

        messages.reverse()

        return [
            {
                "role": "assistant" if msg.sender_id == context.agent.id else "user",
                "content": msg.content,
            }
            for msg in messages
        ]

    def build_message_task(
        self, provider_name: MessagingProviderType, room_id: str, type: MessageTaskType
    ):
        context = self._get_context_from_room_id(room_id)
        messaging_provider = self._get_messaging_provider_from_context(
            context, provider_name
        )

        recent_messages = self._get_recent_messages(context)

        if type == MessageTaskType.RESPONSE:
            from datetime import datetime, timedelta

            return ResponseTask(
                context=context,
                messaging_provider=messaging_provider,
                scheduled_for=datetime.now() + timedelta(seconds=0),
                recent_messages=recent_messages,
            )
        elif type == MessageTaskType.PROACTIVE:
            return ProactiveTask(
                context=context,
                messaging_provider=messaging_provider,
                recent_messages=recent_messages,
            )

        pass

    def _get_context_from_room_id(self, room_id) -> Context:
        room = self.database_manager.get_row(
            Tables.ROOMS, conditions={Tables.ROOMS__id: room_id}
        )
        if not room:
            raise ValueError(f"Room for {room_id} doesn't exist.")
        user = self.database_manager.get_row(
            Tables.USERS,
            conditions={Tables.USERS__id: room.user_id},
        )
        agent = self.database_manager.get_row(
            Tables.AGENTS,
            conditions={Tables.AGENTS__id: room.agent_id},
        )
        return Context(
            user=user,
            agent=agent,
            room=room,
        )

    def _get_messaging_provider_from_context(
        self, context: Context, provider_name: MessagingProviderType
    ) -> MessagingProvider:
        """Returns a properly configured messaging provider class"""

        messaging_provider = messaging_providers.get(provider_name)
        if not messaging_provider:
            raise ValueError(f"Invalid messaging provider: {provider_name}")

        if isinstance(messaging_provider, BirdMessaging):

            messaging_provider.set_receiver(context.user.phone_number)
            messaging_provider.set_sender(context.agent.bird_channel_id)

        elif isinstance(messaging_provider, InstagramMessaging):

            account = self.database_manager.get_row(
                Tables.IGACCOUNTS,
                {Tables.IGACCOUNTS__agent_id: context.agent.id},
            )

            if not account:
                raise ValueError(
                    f"No Instagram account found for agent: {context.agent.id}"
                )

            # TODO: set a User's instagram account id (set_receiver)
            messaging_provider.set_sender(account.account_id)
            messaging_provider._access_token = account.access_token

        else:
            raise NotImplementedError

        return messaging_provider

    def _get_context_from_message(self, message: MiniMessage) -> Context:

        user, agent = self._get_user_and_agent_from_db(message)

        if user is None:
            user = self.user_table_service.create_user(
                id=str(
                    uuid.uuid4()
                ),  # If user verifies later, this will be replaced with Supabase Auth uuid
                phone_number=(
                    message.metadata.receiver_id
                    if message.provider == MessagingProviderType.BIRD
                    else None
                ),
            )

        room = self._get_or_create_room(user, agent)

        return Context(
            user=user,
            agent=agent,
            room=room,
        )

    def _get_user_and_agent_from_db(
        self, message: MiniMessage
    ) -> Tuple[Optional[User], Agent]:
        user = None
        agent = None
        user_id_col = None
        agent_id_col = None

        if message.provider == MessagingProviderType.TELEGRAM:
            user_id_col = Tables.USERS__telegram_uid
            # not implemented:
            # agent_id_col = Tables.USERS__telegram_chat_id
        elif message.provider == MessagingProviderType.BIRD:
            user_id_col = Tables.USERS__phone_number
            agent_id_col = Tables.AGENTS__bird_channel_id

            # If bird channel id is equal to the dev channel ids, use the config room variable

        elif message.provider == MessagingProviderType.INSTAGRAM:
            # user_id_col = Tables.USERS__ig_account # not implemented
            agent_id_col = Tables.IGACCOUNTS__account_id

        user = self.database_manager.get_row(
            Tables.USERS,
            conditions={user_id_col: message.metadata.receiver_id},
        )
        agent = self.database_manager.get_row(
            Tables.AGENTS,
            conditions={agent_id_col: message.metadata.sender_id},
        )

        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        return user, agent

    def _get_or_create_room(self, user: User, agent: Agent) -> Room:
        room = self.database_manager.get_row(
            Tables.ROOMS,
            conditions={
                Tables.ROOMS__user_id: user.id,
                Tables.ROOMS__agent_id: agent.id,
            },
        )
        if not room:
            room = Room(user_id=user.id, agent_id=agent.id)
            room = self.database_manager.insert(Tables.ROOMS, room)
        return room
