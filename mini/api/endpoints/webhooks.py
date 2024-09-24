from fastapi import (
    APIRouter,
    Request,
    Response,
    HTTPException,
    Depends,
    BackgroundTasks,
)
from mini.core.logger import get_logger
from mini.core.models.message import MessagingProviderEnum

from fastapi import Depends

from config.config import config
from mini.messaging.providers.bird.models import BirdRequest
from mini.messaging.providers.instagram.webhook import InstagramWebhookService
from mini.messaging.providers.instagram.dependencies import validate_instagram_webhook
from mini.messaging.providers.instagram.models import InstagramWebhook
from mini.database.database import DatabaseManager
from mini.messaging.tasks.tasks import send_response


router = APIRouter(
    prefix="/webhooks",
    tags=["webhooks"],
)
logger = get_logger(__name__)


@router.post("/bird")
async def bird_webhook(
    request: BirdRequest,
):
    """Endpoint hit by incoming user messages."""
    send_response.delay(MessagingProviderEnum.BIRD.value, request.model_dump())
    return {"status": "Success"}


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
    webhook: InstagramWebhook = Depends(validate_instagram_webhook),
    database_manager: DatabaseManager = Depends(DatabaseManager),
):
    """Instagram events for any of our characters hit this endpoint"""
    service = InstagramWebhookService(database_manager)
    return service.handle_webhook(webhook)
