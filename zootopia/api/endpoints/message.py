from fastapi import APIRouter, Request, HTTPException
from zootopia.core.logger import logger
from zootopia.controller.tasks.respond import handle_respond

router = APIRouter()


@router.post("/message")
async def message_webhook(
    request: Request,
):
    try:
        request_body = await request.json()
        handle_respond(request_body)
        return {"status": "Message received and processing scheduled"}
    except Exception as e:
        logger.exception("Error in message_webhook")
        raise HTTPException(status_code=500, detail=str(e))
