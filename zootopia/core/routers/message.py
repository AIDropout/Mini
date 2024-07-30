from fastapi import APIRouter, Request, HTTPException, Depends
from zootopia.core.logger import logger
from zootopia.server.message_handler import MessageHandler
from config.config import config
from zootopia.server.celery.tasks import process_task
import json

router = APIRouter()

def get_scheduler():
    return MessageHandler(config)

@router.post("/message")
async def message_webhook(
    request: Request,
    handler: MessageHandler = Depends(get_scheduler),
):
    try:
        request_body = await request.json()
        handler.schedule_respond(request_body)
        return {"status": "Message received and processing scheduled"}
    except Exception as e:
        logger.exception("Error in message_webhook")
        raise HTTPException(status_code=500, detail=str(e))