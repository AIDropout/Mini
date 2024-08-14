from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, Security
from zootopia.api.security import verify_api_key
from zootopia.controller.tasks.respond import handle_respond
from zootopia.controller.tasks.revive import handle_revive
from zootopia.utils.utils import is_ngrok_url
from zootopia.core.logger import logger
from zootopia.controller.context.cron import CronContextManager
from zootopia.core.schema import (
    Tables,
    Message,
)

router = APIRouter(prefix="/room", tags=["room"])


@router.post("/respond")
async def respond_webhook(request: Request):
    """Endpoint hit by incoming user messages."""
    try:
        request_body = await request.json()
        handle_respond(request_body)
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
        await handle_revive(
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
        room_id = payload.get("room_id")
        message = payload.get("message")

        if not room_id or not message:
            raise HTTPException(status_code=400, detail="Missing room_id or message")

        context = CronContextManager(room_id)

        new_message = Message(
            sender_id=context.room.agent_id,
            room_id=room_id,
            content=message,
            sent_by_admin=True,
        )

        context.database.insert(table_name=Tables.MESSAGES.value, item=new_message)
        await context.messaging_service.send_message(message)

        return {"status": "Admin message sent successfully"}
    except Exception as e:
        logger.exception("Error in send_admin_message")
        raise HTTPException(status_code=500, detail=str(e))
