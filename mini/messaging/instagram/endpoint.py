from fastapi import (
    APIRouter,
    Request,
    Response,
    HTTPException,
    Depends,
    BackgroundTasks,
)

from config.config import config
from mini.core.logger import get_logger
from mini.messaging.instagram.webhook import InstagramWebhookService
from mini.messaging.instagram.dependencies import validate_instagram_webhook
from mini.messaging.instagram.models import InstagramWebhook
from mini.messaging.dependencies import MessagingServiceDep
from mini.database.database import DatabaseManager

router = APIRouter(prefix="/webhooks")
logger = get_logger(__name__)


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
    messaging_service: MessagingServiceDep,
    background_tasks: BackgroundTasks,
    webhook: InstagramWebhook = Depends(validate_instagram_webhook),
    database_manager: DatabaseManager = Depends(DatabaseManager),
):
    """Instagram events for any of our characters hit this endpoint"""
    service = InstagramWebhookService(messaging_service, database_manager)
    return service.handle_webhook(webhook, background_tasks)
