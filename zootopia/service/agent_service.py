from fastapi import HTTPException
from zootopia.manager.database import DatabaseManager
from zootopia.manager.payment.customer import CustomerManager
from zootopia.core.schema.tables import Tables, User
from zootopia.service.base import Service
from fastapi.responses import JSONResponse
from postgrest.exceptions import APIError


class AgentService(Service):
    def __init__(self, database_manager: DatabaseManager):
        super().__init__(database_manager)

    def get_agents(self) -> User:
        agents = self.database_manager.get_multiple_rows(
            Tables.AGENTS,
        )
        if not agents:
            raise HTTPException(status_code=404, detail="Agents not found")
        return agents
