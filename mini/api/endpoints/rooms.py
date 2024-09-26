from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path

from config.container import container
from mini.api.security import ApiKeyDep
from mini.core.logger import get_logger
from mini.core.models.message import MessagingProviderType
from mini.database.models import Room
from mini.database.service.room_service import RoomService
from mini.messaging.tasks.tasks import send_message
from mini.messaging.tasks.models import MessageTaskType
from mini.server.celery.celery import app


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
async def proactive_endpoint(
    api_key: ApiKeyDep,
    room_id: Annotated[str, Path(..., title="Room ID for proactive messaging")],
):
    logger.info(app.tasks)
    """Endpoint for sending proactive messages."""
    send_message.delay(
        provider_name=MessagingProviderType.BIRD.value,
        room_id=room_id,
        type=MessageTaskType.PROACTIVE.value,
    )
    return {"status": "Success"}
