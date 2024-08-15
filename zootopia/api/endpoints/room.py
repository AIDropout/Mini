from fastapi import (
    APIRouter,
    Request,
    BackgroundTasks,
    HTTPException,
    Security,
    Depends,
)
from zootopia.service.reply_service import ReplyService
from zootopia.service.cron_service import CronService
from zootopia.api.security import verify_api_key
from zootopia.utils.utils import is_ngrok_url
from zootopia.core.logger import logger
from config.container import container

router = APIRouter(prefix="/room", tags=["room"])


def get_reply_service() -> ReplyService:
    return container.reply_service


def get_cron_service() -> CronService:
    return container.cron_service


@router.post("/respond")
async def respond_webhook(
    request: Request,
    reply_service: ReplyService = Depends(get_reply_service),
):
    """Endpoint hit by incoming user messages."""
    try:
        request_body = await request.json()
        reply_service.handle_respond(request_body)
        return {"status": "Message received and processing scheduled"}
    except Exception as e:
        logger.exception("Error in respond_webhook")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/revive")
async def revive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    cron_service: CronService = Depends(get_cron_service),
    api_key: str = Security(verify_api_key),
):
    """Endpoint hit by Supabase cron job every x minutes."""
    try:
        await cron_service.refresh_rooms(
            background_tasks, dev_mode=is_ngrok_url(str(request.base_url))
        )
        return {"status": "Revive process initiated"}
    except Exception as e:
        logger.exception(f"Error in revive webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin-message")
async def send_admin_message(
    request: Request,
    reply_service: ReplyService = Depends(get_reply_service),
    api_key: str = Security(verify_api_key),
):
    """Endpoint for sending messages from the admin dashboard."""
    try:
        payload = await request.json()
        await reply_service.send_admin_message(payload)
        return {"status": "Admin message sent successfully"}
    except Exception as e:
        logger.exception("Error in send_admin_message")
        raise HTTPException(status_code=500, detail=str(e))
