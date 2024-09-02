from typing import List

from fastapi import APIRouter, Depends, HTTPException, Security

from config.container import container
from mini.api.security import verify_api_key
from mini.core.logger import logger
from mini.core.schema.tables import Agent
from mini.service.agent_service import AgentService

router = APIRouter()


@router.get("/agents", response_model=List[Agent])
async def get_agents(
    agent_service: AgentService = Depends(lambda: container.get_agent_service()),
    api_key: str = Security(verify_api_key),
) -> List[Agent]:
    """Get all agents. Returns a list of Agents to be displayed on the production frontend"""
    agents = agent_service.get_agents()
    if not agents:
        raise HTTPException(status_code=404, detail="No agents found")
    logger.info(agents)
    return agents
