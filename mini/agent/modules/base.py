from abc import ABC

from mini.database.models import Agent, Room, User
from mini.database.database import DatabaseManager


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
