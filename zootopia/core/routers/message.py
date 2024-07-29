from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from zootopia.core.logger import logger
from zootopia.server.background import schedule_respond

router = APIRouter()


@router.post("/message")
async def message_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        request_body = await request.json()
        logger.info(f"]Received request body: {request_body}")
        background_tasks.add_task(schedule_respond, request_body)
        return {"status": "Message received and processing scheduled"}
    except Exception as e:
        logger.exception("Error in message_webhook")
        raise HTTPException(status_code=500, detail=str(e))
