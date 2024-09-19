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
from mini.api.security import ApiKeyDep
from mini.core.logger import get_logger
from mini.core.schema.tables import Room
from mini.service.dashboard_service import DashboardService
from mini.service.reply_service import ReplyService
from mini.service.room_service import RoomService

router = APIRouter()
logger = get_logger(__name__)

RoomServiceDep = Annotated[RoomService, Depends(lambda: container.get_room_service())]
ReplyServiceDep = Annotated[
    ReplyService, Depends(lambda: container.get_reply_service())
]
DashboardServiceDep = Annotated[
    DashboardService, Depends(lambda: container.get_dashboard_service())
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


@router.post("/rooms/respond")
async def respond_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    reply_service: ReplyServiceDep,
):
    """Endpoint hit by incoming user messages."""
    request_body = await request.json()
    reply_service.handle_respond(request_body, background_tasks)


@router.post("/rooms/admin-message")
def send_admin_message(
    room_id: Annotated[
        str, Body(..., title="Room ID of the page the user signed up to")
    ],
    message: Annotated[str, Body(..., title="Message to send to user")],
    dashboard_service: DashboardServiceDep,
    api_key: ApiKeyDep,
):
    """Endpoint for sending messages from the admin dashboard."""
    dashboard_service.send_admin_message(room_id, message)
