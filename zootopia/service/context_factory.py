from typing import Optional
from zootopia.core.schema import (
    Agent,
    Room,
    User,
    Tables,
    ZootopiaMessage,
    MessageProvider,
)
from zootopia.manager.database import DatabaseManager
from zootopia.core.exceptions import AgentNotFoundError
from dataclasses import dataclass, field
from zootopia.manager.messaging.factory import MessagingManagerFactory
from zootopia.service.base import Service


@dataclass
class Context:
    user: Optional[User] = None
    agent: Optional[Agent] = None
    room: Optional[Room] = None


class ContextFactory(Service):
    def __init__(self, database_manager: DatabaseManager):
        super().__init__(database_manager)
        self.messaging_manager_factory = MessagingManagerFactory()

    def create_cron_context(self, room_id) -> Context:
        room = self.database_manager.get_row(
            Tables.ROOMS.value, conditions={Tables.ROOMS__id.value: room_id}
        )
        user = self.database_manager.get_row(
            Tables.USERS.value,
            conditions={Tables.USERS__id.value: room.user_id},
        )
        agent = self.database_manager.get_row(
            Tables.AGENTS.value,
            conditions={Tables.AGENTS__id.value: room.agent_id},
        )

        return Context(
            user=user,
            agent=agent,
            room=room,
        )

    def create_message_context(self, message: ZootopiaMessage) -> Context:

        user, agent = self._get_user_and_agent_from_db(message)
        room = self._get_or_create_room(user, agent)

        return Context(
            user=user,
            agent=agent,
            room=room,
        )

    def _get_user_and_agent_from_db(self, message: ZootopiaMessage):
        user = None
        agent = None

        if message.provider == MessageProvider.TELEGRAM:
            user = self.database_manager.get_row(
                Tables.USERS.value,
                conditions={Tables.USERS__telegram_uid.value: message.metadata.uid},
            )
            agent = self.database_manager.get_row(
                Tables.AGENTS.value,
                conditions={
                    Tables.AGENTS__telegram_chat_id.value: message.metadata.chat_id
                },
            )
        elif message.provider == MessageProvider.BIRD:
            user = self.database_manager.get_row(
                Tables.USERS.value,
                conditions={
                    Tables.USERS__phone_number.value: message.metadata.phone_number
                },
            )
            agent = self.database_manager.get_row(
                Tables.AGENTS.value,
                conditions={
                    Tables.AGENTS__bird_channel_id.value: message.metadata.channel_id
                },
            )

        if not user:
            user = self._create_new_user(message)

        if not agent:
            raise AgentNotFoundError(
                f"Couldn't retrieve agent. Make sure the agent row matches incoming metadata: {message.metadata}"
            )

        return user, agent

    def _create_new_user(self, message: ZootopiaMessage) -> User:
        new_user = User(
            telegram_uid=(
                message.metadata.uid
                if message.provider == MessageProvider.TELEGRAM
                else None
            ),
            phone_number=(
                message.metadata.phone_number
                if message.provider == MessageProvider.BIRD
                else None
            ),
        )
        return self.database_manager.insert(Tables.USERS.value, new_user)

    def _get_or_create_room(self, user: User, agent: Agent) -> Room:
        room = self.database_manager.get_row(
            Tables.ROOMS.value,
            conditions={
                Tables.ROOMS__user_id.value: user.id,
                Tables.ROOMS__agent_id.value: agent.id,
            },
        )
        if not room:
            room = Room(user_id=user.id, agent_id=agent.id)
            room = self.database_manager.insert(Tables.ROOMS.value, room)
        return room
