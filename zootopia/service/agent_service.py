from fastapi import HTTPException
from zootopia.manager.database import DatabaseManager
from zootopia.core.schema.tables import Tables, Agent
from zootopia.service.base import Service
from typing import List


class AgentService(Service):
    def __init__(self, database_manager: DatabaseManager):
        super().__init__(database_manager)

    def get_agents(self) -> List[Agent]:
        agents = self.database_manager.get_multiple_rows(
            Tables.AGENTS,
            order_by="id",
            max_rows=100,
            conditions={Tables.AGENTS__show_on_site: True},
        )
        if not agents:
            raise HTTPException(status_code=404, detail="Agents not found")
        return [Agent(**agent) for agent in agents]
