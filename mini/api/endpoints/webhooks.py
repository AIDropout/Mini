from typing import Annotated
import random
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    BackgroundTasks,
)

from config.config import config
from config.container import container
from mini.core.enums import MessagingProviderType
from mini.core.logger import get_logger
from mini.messaging.providers.bird.models import BirdRequest
from mini.messaging.providers.instagram.dependencies import validate_instagram_webhook
from mini.messaging.providers.instagram.models import InstagramWebhook
from mini.messaging.providers.instagram.webhook import InstagramWebhookService
from mini.messaging.service import MessagingService

router = APIRouter(
    prefix="/webhooks",
    tags=["webhooks"],
)
logger = get_logger(__name__)
MessagingServiceDep = Annotated[
    MessagingService, Depends(lambda: container.messaging_service)
]


@router.post("/bird")
async def bird_inbound_webhook(
    request: BirdRequest,
    messaging_service: MessagingServiceDep,
    background_tasks: BackgroundTasks,
):
    """Endpoint hit by incoming user messages."""
    messaging_service.handle_incoming_message(
        MessagingProviderType.BIRD, request.model_dump(), background_tasks
    )
    return {"status": "Success"}


@router.post("/bird/outbound")
async def bird_outbound_webhook(request: BirdRequest):
    logger.info(request)


@router.get("/instagram")
async def verify_instagram_webhook(request: Request):
    """Called by Instagram to verify our webhook is properly setup"""
    VERIFY_TOKEN = config.INSTAGRAM_CONFIG.verify_token

    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return Response(content=challenge)
        else:
            raise HTTPException(status_code=403, detail="Invalid verify token")

    raise HTTPException(status_code=400, detail="Missing parameters")


@router.post("/instagram")
def handle_instagram_webhook(
    background_tasks: BackgroundTasks,
    messaging_service: MessagingServiceDep,
    webhook: InstagramWebhook = Depends(validate_instagram_webhook),
):
    """Instagram events for any of our characters hit this endpoint"""
    service = InstagramWebhookService(messaging_service, background_tasks)
    return service.handle_webhook(webhook)
