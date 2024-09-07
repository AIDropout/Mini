from typing import List

from fastapi import HTTPException

from mini.core.schema.tables import Agent, Tables
from mini.manager.database import DatabaseManager
from mini.service.base import Service


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
        return agents
