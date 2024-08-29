from fastapi import APIRouter, Depends, Security, HTTPException
from zootopia.api.security import verify_api_key
from zootopia.core.schema.tables import Agent
from config.container import container
from zootopia.service.agent_service import AgentService
from typing import List
from zootopia.core.logger import logger

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
