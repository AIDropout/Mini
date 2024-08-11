from fastapi import APIRouter, Request, HTTPException, Security
from zootopia.core.security import verify_api_key
from zootopia.core.logger import logger
from zootopia.core.schema import (
    Tables,
    MessageTableModel,
)
from zootopia.controller.context.cron import CronContextManager


router = APIRouter()


@router.post("/dashboard")
async def send_msg_from_dash(request: Request, api_key: str = Security(verify_api_key)):
    """Endpoint for sending messages from the dashboard."""
    try:
        payload = await request.json()
        room_id = payload.get("room_id")
        message = payload.get("message")

        context = CronContextManager(room_id)

        new_message = MessageTableModel(
            sender_id=context.room.agent_id,
            room_id=room_id,
            content=message,
            sent_by_admin=True,
        )

        context.database.insert(table_name=Tables.MESSAGES.value, item=new_message)
        await context.messaging_service.send_message(message)

    except Exception as e:
        logger.exception("Error in send_msg_from_dash")
        raise HTTPException(status_code=500, detail=str(e))
