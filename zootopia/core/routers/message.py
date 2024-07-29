from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, Depends
from zootopia.core.logger import logger
from zootopia.server.redis import redis
from zootopia.server.scheduler import TaskScheduler
from config.config import config

router = APIRouter()


def get_scheduler():
    return TaskScheduler(config, redis)


@router.post("/message")
async def message_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    scheduler: TaskScheduler = Depends(get_scheduler),
):
    try:
        request_body = await request.json()
        background_tasks.add_task(scheduler.schedule_respond, request_body)
        return {"status": "Message received and processing scheduled"}
    except Exception as e:
        logger.exception("Error in message_webhook")
        raise HTTPException(status_code=500, detail=str(e))
