from typing import Annotated, Optional

from fastapi import APIRouter, Body, Depends, BackgroundTasks

from config.container import container
from mini.api.security import ApiKeyDep
from mini.core.logger import get_logger
from mini.database.models import Room
from mini.database.tables.room_service import RoomTableService


RoomTableServiceDep = Annotated[
    RoomTableService, Depends(lambda: container.room_table_service)
]

router = APIRouter(
    tags=["rooms"],
)
logger = get_logger(__name__)


@router.post("/rooms")
def create_room(
    agent_id: Annotated[
        str, Body(..., title="Agent ID of the page the user signed up to")
    ],
    user_id: Annotated[str, Body(..., title="The user's ID")],
    room_service: RoomTableServiceDep,
    api_key: ApiKeyDep,
    background_tasks: BackgroundTasks,
    first_message: Annotated[
        str, Body(title="Optional first message to send to the user")
    ] = None,
) -> Room:
    """Creates a room and sends the first message to the user"""
    return room_service.create_room(
        agent_id=agent_id,
        user_id=user_id,
        first_message=first_message,
        background_tasks=background_tasks,
    )
