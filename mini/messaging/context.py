import uuid
from typing import Optional, Tuple

from fastapi import HTTPException

from mini.core.models.context import Context
from mini.core.models.message import MessagingProviderEnum, MiniMessage
from mini.database.models import Agent, Room, Tables, User
from mini.database.database import DatabaseManager
from mini.database.service.user_service import UserService
from mini.messaging.provider import MessagingProvider, messaging_providers
from mini.messaging.provider.bird.bird import BirdMessaging
from mini.messaging.provider.instagram.instagram import InstagramMessaging


class ContextFactory:
    def __init__(
        self, database_manager: DatabaseManager, user_service: UserService
    ) -> None:
        self.database_manager = database_manager
        self.user_service = user_service

    def get_context_from_room_id(self, room_id) -> Context:
        room = self.database_manager.get_row(
            Tables.ROOMS, conditions={Tables.ROOMS__id: room_id}
        )
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

    def get_messaging_provider_from_context(
        self, context: Context, provider_name: MessagingProviderEnum
    ) -> MessagingProvider:
        """Returns a properly configured messaging provider class"""

        messaging_provider = messaging_providers.get(provider_name)
        if not messaging_provider:
            raise ValueError(f"Invalid messaging provider: {provider_name}")

        if isinstance(messaging_provider, BirdMessaging):

            messaging_provider.set_receiver(context.agent.bird_channel_id)
            messaging_provider.set_sender(context.user.phone_number)

        elif isinstance(messaging_provider, InstagramMessaging):

            account = self.database_manager.get_row(
                Tables.IGACCOUNTS,
                {Tables.IGACCOUNTS__agent_id: context.agent.id},
            )

            if not account:
                raise ValueError(
                    f"No Instagram account found for agent: {context.agent.id}"
                )

            # TODO: set a User's instagram account id
            messaging_provider.set_sender = account.account_id
            messaging_provider._access_token = account.access_token

        else:
            raise NotImplementedError

        return messaging_provider

    # TODO: GIVEN provider_name & room_id, get receiver-sender info

    def get_context_from_message(self, message: MiniMessage) -> Context:

        user, agent = self._get_user_and_agent_from_db(message)

        if user is None:
            user = self.user_service.create_user(
                id=str(
                    uuid.uuid4()
                ),  # If user verifies later, this will be replaced with Supabase Auth uuid
                phone_number=(
                    message.metadata.receiver_id
                    if message.provider == MessagingProviderEnum.BIRD
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

        if message.provider == MessagingProviderEnum.TELEGRAM:
            user_id_col = Tables.USERS__telegram_uid
            # not implemented:
            # agent_id_col = Tables.USERS__telegram_chat_id
        elif message.provider == MessagingProviderEnum.BIRD:
            user_id_col = Tables.USERS__phone_number
            agent_id_col = Tables.AGENTS__bird_channel_id
        elif message.provider == MessagingProviderEnum.INSTAGRAM:
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
