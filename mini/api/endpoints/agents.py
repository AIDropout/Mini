from typing import List, Annotated
from fastapi import APIRouter, Depends, Path, Body

from config.container import container
from mini.api.security import ApiKeyDep
from mini.core.logger import get_logger
from mini.database.models import Agent
from mini.database.tables.agent_service import AgentTableService

router = APIRouter(
    prefix="/agents",
    tags=["agents"],
)
logger = get_logger(__name__)

AgentTableServiceDep = Annotated[
    AgentTableService, Depends(lambda: container.get_agent_table_service())
]


@router.get("/", response_model=List[Agent])
def get_agents(
    agent_service: AgentTableServiceDep,
    api_key: ApiKeyDep,
) -> List[Agent]:
    """Get all agents. Returns a list of Agents to be displayed on the production frontend"""
    return agent_service.get_agents()


@router.patch("/{agent_id}", response_model=Agent)
def update_agent(
    agent_id: Annotated[str, Path(..., title="The ID of the agent to update")],
    agent_update: Annotated[
        dict,
        Body(..., title="The fields to update. Only the updated fields are needed."),
    ],
    agent_service: AgentTableServiceDep,
    api_key: ApiKeyDep,
) -> Agent:
    return agent_service.update_agent(agent_id=agent_id, update_data=agent_update)
