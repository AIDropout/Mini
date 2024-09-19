from abc import ABC

from mini.core.schema.tables import Agent, Room, User
from mini.storage.database import DatabaseManager


class AgentModule(ABC):
    def __init__(self, database_manager: DatabaseManager):
        self.database_manager = database_manager
        self.room: Room = None
        self.agent: Agent = None
        self.user_id: User = None

    def configure(self, room: Room, agent: Agent, user: User):
        self.room = room
        self.agent = agent
        self.user = user
