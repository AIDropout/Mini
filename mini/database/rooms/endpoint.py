from fastapi import (
    APIRouter,
    Body,
    Depends,
    Path,
    Request,
    BackgroundTasks
)
from typing import Annotated

from config.container import container
from mini.core.security import ApiKeyDep
from mini.core.logger import get_logger
from mini.database.models import Room
from mini.messaging.service import ReplyService
from mini.database.rooms.service import RoomService

router = APIRouter()
logger = get_logger(__name__)

RoomServiceDep = Annotated[RoomService, Depends(lambda: container.get_room_service())]
ReplyServiceDep = Annotated[
    ReplyService, Depends(lambda: container.get_reply_service())
]


@router.get("/rooms/{user_id}")
def get_rooms(
    user_id: Annotated[str, Path(..., title="The user's ID")],
    room_service: RoomServiceDep,
    api_key: ApiKeyDep,
) -> Room:
    """Creates a room and sends the first message to the user"""
    return room_service.get_user_rooms(user_id=user_id)


@router.post("/rooms")
def create_room(
    agent_id: Annotated[
        str, Body(..., title="Agent ID of the page the user signed up to")
    ],
    user_id: Annotated[str, Body(..., title="The user's ID")],
    room_service: RoomServiceDep,
    api_key: ApiKeyDep,
) -> Room:
    """Creates a room and sends the first message to the user"""
    return room_service.create_room(agent_id=agent_id, user_id=user_id)