from fastapi import APIRouter, Depends, Security
from zootopia.api.security import verify_api_key
from zootopia.core.schema.tables import Agent
from config.container import container
from zootopia.service.agent_service import AgentService
from typing import List


router = APIRouter()


@router.get("/agents", response_model=List[Agent])
async def get_agents(
    agent_service: AgentService = Depends(lambda: container.get_agent_service()),
    api_key: str = Security(verify_api_key),
) -> List[Agent]:
    """Get a user by ID. Returns the retrieved User object"""
    return agent_service.get_agents()
