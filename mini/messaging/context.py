import uuid
from dataclasses import dataclass
from typing import Optional, Tuple

from fastapi import HTTPException

from mini.messaging.models import MessageProvider, MiniMessage
from mini.database.models import Agent, Room, Tables, User
from mini.database.database import DatabaseManager
from mini.database.users.service import UserService


@dataclass
class Context:
    user: Optional[User] = None
    agent: Optional[Agent] = None
    room: Optional[Room] = None


class ContextFactory():
    def __init__(self, database_manager: DatabaseManager, user_service: UserService):
        self.database_manager = database_manager
        self.user_service = user_service

    def create_cron_context(self, room_id) -> Context:
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

    def create_message_context(self, message: MiniMessage) -> Context:

        user, agent = self._get_user_and_agent_from_db(message)

        if user is None:
            user = self.user_service.create_user(
                id=str(
                    uuid.uuid4()
                ),  # If user verifies later, this will be replaced with Supabase Auth uuid
                phone_number=(
                    message.metadata.phone_number
                    if message.provider == MessageProvider.BIRD
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

        if message.provider == MessageProvider.TELEGRAM:
            user = self.database_manager.get_row(
                Tables.USERS,
                conditions={Tables.USERS__telegram_uid: message.metadata.uid},
            )
            # agent = self.database_manager.get_row(
            #     Tables.AGENTS,
            #     conditions={Tables.AGENTS__telegram_chat_id: message.metadata.chat_id},
            # ) # Add telegram_chat_id back to agents table if we end up adding this integration
        elif message.provider == MessageProvider.BIRD:
            user = self.database_manager.get_row(
                Tables.USERS,
                conditions={Tables.USERS__phone_number: message.metadata.phone_number},
            )
            agent = self.database_manager.get_row(
                Tables.AGENTS,
                conditions={
                    Tables.AGENTS__bird_channel_id: message.metadata.channel_id
                },
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
