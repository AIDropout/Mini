from zootopia.manager.database import DatabaseManager


class Service:
    def __init__(self, database_manager: DatabaseManager):
        self.database_manager = database_manager
