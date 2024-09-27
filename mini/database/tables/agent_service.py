from typing import List, Dict, Any

from fastapi import HTTPException

from config.config import config
from mini.database.models import Agent, Tables
from mini.database.database import DatabaseManager


class AgentTableService:
    def __init__(self, database_manager: DatabaseManager):
        self.database_manager = database_manager

    def get_agents(self) -> List[Agent]:
        agents = self.database_manager.get_multiple_rows(
            Tables.AGENTS,
            order_by="id",
            max_rows=100,
        )
        if not agents:
            raise HTTPException(status_code=404, detail="Agents not found")

        # Filter out agents with specific channel IDs
        excluded_channel_ids = [
            config.PHONE_OTP_CHANNEL_ID,
            "946f4f9d-21c0-495e-b59d-5f3704deb11b",
            "5a075672-763c-51df-aba6-82eecdceab72"
        ]
        filtered_agents = [
            agent for agent in agents
            if agent.bird_channel_id not in excluded_channel_ids
        ]

        if not filtered_agents:
            raise HTTPException(
                status_code=404, detail="No valid agents found after filtering"
            )

        return filtered_agents

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

