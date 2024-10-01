from typing import Annotated
import random
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from config.config import config
from config.container import container
from mini.core.enums import MessageTaskType
from mini.core.logger import get_logger
from mini.core.models.message import MessagingProviderType
from mini.database.database import DatabaseManager
from mini.messaging.providers.bird.models import BirdRequest
from mini.messaging.providers.instagram.dependencies import validate_instagram_webhook
from mini.messaging.providers.instagram.models import InstagramWebhook
from mini.messaging.providers.instagram.webhook import InstagramWebhookService
from mini.messaging.send_message.send_message import send_message
from mini.messaging.service import MessagingService
from mini.server.celery.celery import app

router = APIRouter(
    prefix="/webhooks",
    tags=["webhooks"],
)
logger = get_logger(__name__)
FactoryDep = Annotated[MessagingService, Depends(lambda: container.messaging_service)]


@router.post("/bird")
async def bird_inbound_webhook(request: BirdRequest, factory: FactoryDep):
    """Endpoint hit by incoming user messages."""
    room_id = factory.process_and_store_incoming_message(
        MessagingProviderType.BIRD, request.model_dump()
    )
    logger.info(app.tasks)

    # Generate a random delay between 3 and 20 seconds
    delay = random.randint(3, 20)

    # 1 in 20 chance that a message response gets scheduled for later.

    # Schedule the message sending with the random delay
    send_message.apply_async(
        kwargs={
            "provider_name": MessagingProviderType.BIRD.value,
            "room_id": room_id,
            "type": MessageTaskType.RESPONSE.value,
        },
        countdown=delay,
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
    factory: FactoryDep,
    webhook: InstagramWebhook = Depends(validate_instagram_webhook),
):
    """Instagram events for any of our characters hit this endpoint"""
    service = InstagramWebhookService(factory)
    return service.handle_webhook(webhook)
