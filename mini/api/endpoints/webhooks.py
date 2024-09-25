from fastapi import (
    APIRouter,
    Request,
    Response,
    HTTPException,
    Depends,
    BackgroundTasks,
    Depends,
    Path
)
from typing import Annotated


from config.config import config
from config.container import container
from mini.core.logger import get_logger
from mini.core.models.message import MessagingProviderType
from mini.messaging.providers.bird.models import BirdRequest
from mini.messaging.providers.instagram.webhook import InstagramWebhookService
from mini.messaging.providers.instagram.dependencies import validate_instagram_webhook
from mini.messaging.providers.instagram.models import InstagramWebhook
from mini.messaging.tasks.factory import MessageTaskFactory
from mini.messaging.tasks.models import MessageTaskType
from mini.database.database import DatabaseManager
from mini.messaging.tasks.tasks import send_message


router = APIRouter(
    prefix="/webhooks",
    tags=["webhooks"],
)
logger = get_logger(__name__)
FactoryDep = Annotated[
    MessageTaskFactory, Depends(lambda: container.get_message_task_factory())
]


@router.post("/bird")
async def bird_webhook(request: BirdRequest, factory: FactoryDep):
    """Endpoint hit by incoming user messages."""
    room_id = factory.process_and_store_incoming_message(
        MessagingProviderType.BIRD, request.model_dump()
    )
    send_message.delay(
        provider_name=MessagingProviderType.BIRD.value,
        room_id=room_id,
        type=MessageTaskType.RESPONSE.value,
    )
    return {"status": "Success"}


# @router.post("/bird/{room_id}/proactive")
# async def bird_webhook(
#     room_id: Annotated[str, Path(..., title="Room ID for proactive messaging")],
# ):
#     """Endpoint hit by incoming user messages."""
#     send_message.delay(
#         provider_name=MessagingProviderType.BIRD.value,
#         room_id=room_id,
#         type=MessageTaskType.PROACTIVE.value,
#     )
#     return {"status": "Success"}


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
    database_manager: DatabaseManager = Depends(DatabaseManager),
):
    """Instagram events for any of our characters hit this endpoint"""
    service = InstagramWebhookService(database_manager, factory)
    return service.handle_webhook(webhook)
