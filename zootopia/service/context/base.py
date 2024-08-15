from typing import Optional
from zootopia.core.schema import Agent, Room, User, Tables
from zootopia.manager.database import DatabaseManager
from zootopia.manager.messaging import MessagingManager

"""
"ContextServices" initialize and hold the managers and objects needed for an agents & its modules.

Think of these as the toolbox for any agent running on the server.

database - allows agent & modules to make supabase calls
messaging_manager - allows agent & modules to send messages
room - holds row data of the room involved
user - holds row data of the user involved
agent - holds row data of the agent involved
"""


class ContextService:
    def __init__(self):
        self.database_manager: DatabaseManager = DatabaseManager()
        self.messaging_manager: MessagingManager = None
        self.user: Optional[User] = None
        self.agent: Optional[Agent] = None
        self.room: Optional[Room] = None

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
            print(f"Created Room: {room}")

            room_dict = (
                room.model_dump()
            )  # Convert to dictionary to ensure serialization
            print(f"Room as dict: {room_dict}")
            room = self.database_manager.insert(Tables.ROOMS.value, room)

        return room

    def __str__(self):
        return f"ContextService(user={self.user}, agent={self.agent}, room={self.room})"
