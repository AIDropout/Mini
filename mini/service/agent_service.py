from typing import List, Dict, Any

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
        )
        if not agents:
            raise HTTPException(status_code=404, detail="Agents not found")
        return agents

    def update_agent(self, agent_id: str, update_data: Dict[str, Any]) -> Agent:
        existing_agent = self.database_manager.get_row(
            Tables.AGENTS, {Tables.AGENTS__id: agent_id}
        )
        if not existing_agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        update_data = {k: v for k, v in update_data.items() if v is not None}

        updated_agent = self.database_manager.update(
            table_name=Tables.AGENTS,
            update_data=update_data,
            condition_key=Tables.AGENTS__id,
            condition_value=agent_id,
        )
        if not updated_agent:
            raise HTTPException(status_code=400, detail="Failed to update agent")
        return updated_agent
