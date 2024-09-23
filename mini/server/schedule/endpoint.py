from typing import Annotated

from fastapi import APIRouter, Path

from mini.core.logger import get_logger
from mini.core.security import ApiKeyDep
from mini.messaging.models import MessagingProviderEnum
from mini.server.schedule.dependencies import ProactiveServiceDep

router = APIRouter()
logger = get_logger(__name__)


@router.post("/rooms/proactive/{room_id}")
def send_proactive_message(
    room_id: Annotated[str, Path(..., title="Room ID for proactive messaging")],
    proactive_service: ProactiveServiceDep,
    api_key: ApiKeyDep,
):
    """Endpoint for sending proactive messages."""
    return proactive_service.send_proactive_message(
        room_id, provider=MessagingProviderEnum.BIRD
    )
