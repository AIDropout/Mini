from fastapi import APIRouter, BackgroundTasks, Request

from mini.core.logger import get_logger
from mini.messaging.dependencies import MessagingServiceDep
from mini.messaging.models import MessagingProviderEnum

router = APIRouter()
logger = get_logger(__name__)


@router.post("/rooms/respond")
async def respond_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    messaging_service: MessagingServiceDep,
):
    """Endpoint hit by incoming user messages."""
    request_body = await request.json()
    messaging_service.handle_incoming_message(
        MessagingProviderEnum.BIRD, request_body, background_tasks
    )
