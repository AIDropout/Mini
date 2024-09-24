from abc import ABC
from mini.database.database import DatabaseManager
from mini.core.models.context import Context


class AgentModule(ABC):
    def __init__(self, database_manager: DatabaseManager, context: Context):
        self.database_manager = database_manager
        self.context = context
