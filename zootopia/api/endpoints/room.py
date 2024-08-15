from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, Security
from zootopia.api.security import verify_api_key
from zootopia.service.message_service import MessageService
from zootopia.service.room_service import RoomService
from zootopia.utils.utils import is_ngrok_url
from zootopia.core.logger import logger

router = APIRouter(prefix="/room", tags=["room"])


@router.post("/respond")
async def respond_webhook(request: Request):
    """Endpoint hit by incoming user messages."""
    try:
        request_body = await request.json()
        message_service = MessageService()
        await message_service.handle_respond(request_body)
        return {"status": "Message received and processing scheduled"}
    except Exception as e:
        logger.exception("Error in respond_webhook")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/revive")
async def revive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    api_key: str = Security(verify_api_key),
):
    """Endpoint hit by Supabase cron job every x minutes."""
    try:
        room_service = RoomService()
        await room_service.handle_revive(
            background_tasks, dev_mode=is_ngrok_url(str(request.base_url))
        )
        return {"status": "Revive process initiated"}
    except Exception as e:
        logger.exception(f"Error in revive webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin-message")
async def send_admin_message(request: Request, api_key: str = Security(verify_api_key)):
    """Endpoint for sending messages from the admin dashboard."""
    try:
        payload = await request.json()
        room_service = RoomService()
        await room_service.send_admin_message(payload)
        return {"status": "Admin message sent successfully"}
    except Exception as e:
        logger.exception("Error in send_admin_message")
        raise HTTPException(status_code=500, detail=str(e))
