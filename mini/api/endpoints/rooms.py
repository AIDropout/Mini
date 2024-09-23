from typing import Annotated

from fastapi import APIRouter, Path, Body, Depends

from config.container import container
from mini.core.logger import get_logger
from mini.api.security import ApiKeyDep
from mini.core.models.message import MessagingProviderEnum
from mini.server.tasks.send_proactive import send_proactive
from mini.database.models import Room
from mini.database.service.room_service import RoomService

RoomServiceDep = Annotated[RoomService, Depends(lambda: container.get_room_service())]

router = APIRouter(
    prefix="/rooms",
    tags=["rooms"],
)
logger = get_logger(__name__)


@router.post("/")
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


@router.post("/{room_id}/proactive")
def proactive_endpoint(
    api_key: ApiKeyDep,
    room_id: Annotated[str, Path(..., title="Room ID for proactive messaging")],
):
    """Endpoint for sending proactive messages."""
    send_proactive.delay(room_id, MessagingProviderEnum.BIRD.value)
    return {"status": "Success"}


# TODO: change this to celery task
# @router.post("/{room_id}/message")
# def send_admin_message(
#     room_id: Annotated[
#         str, Path(..., title="Room ID of the page the user signed up to")
#     ],
#     message: Annotated[str, Body(..., title="Message to send to user")],
#     dashboard_service: Annotated[
#         DashboardService, Depends(lambda: container.get_dashboard_service())
#     ],
#     api_key: ApiKeyDep,
# ):
#     """Endpoint for sending messages from the admin dashboard."""
#     dashboard_service.send_admin_message(room_id, message)
