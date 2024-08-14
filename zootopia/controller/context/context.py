from typing import Optional
from zootopia.core.schema import Agent, Room, User, Tables
from zootopia.services import MessageProvider, SupabaseDB

"""
"ContextManagers" initialize and hold the utilities needed for an agents & its modules.

Think of these as the toolbox for any function running on the server.

database - allows agent & modules to make supabase calls
messaging_service - allows agent & modules to send messages
room - holds row data of the room involved
user - holds row data of the user involved
agent - holds row data of the agent involved
"""


class BaseContextManager:
    def __init__(self):
        self.database: SupabaseDB = SupabaseDB()
        self.messaging_service: Optional[MessageProvider] = None
        self.user: Optional[User] = None
        self.agent: Optional[Agent] = None
        self.room: Optional[Room] = None

    def _get_or_create_room(self, user: User, agent: Agent) -> Room:
        room = self.database.get_row(
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
            room = self.database.insert(Tables.ROOMS.value, room)

        return room

    def __str__(self):
        return f"ContextManager(user={self.user}, agent={self.agent}, room={self.room})"
