from celery import Celery
from zootopia.context import MessageContextManager, CronContextManager
from zootopia.core.schema import RespondTask, RemindTask, ReviveTask, TaskType
from zootopia.agent.agent import Agent
from config.config import config

from celery import Celery
from datetime import datetime
import json
from zootopia.server.redis import redis_client
from zootopia.agent.agent import Agent
from zootopia.core.logger import logger
from config.config import config

celery_app = Celery('zootopia')

@celery_app.task
def process_task(task):
    try:
        data = json.loads(task)
        room_id = data.get("room_id")
        message = data.get("message")
        timestamp = data.get("creation_time")

        # Create a unique key for this specific request
        request_key = f"request:{room_id}:{message}:{timestamp}"

        # Try to acquire a lock for this room
        with redis_client.lock(f"lock:{room_id}", blocking_timeout=5):
            # Check if this request has already been processed
            if redis_client.get(request_key):
                logger.info(f"Request {request_key} already processed. Skipping.")
                redis_client.zrem("scheduled", task)
                return

            # Mark this request as being processed
            redis_client.setex(request_key, 60, "processing")  # 60 seconds TTL

            # Your existing task processing logic goes here
            context, task_obj = create_task_and_context(data)
            if task_obj is None or context is None:
                redis_client.zrem("scheduled", task)
                return

            agent = Agent.from_config(config, context)
            success = agent.handle_chat_task(task_obj)

            if success:
                # Mark the request as completed
                redis_client.setex(request_key, 3600, "completed")  # 1 hour TTL
                redis_client.zrem("scheduled", task)
            else:
                # If failed, allow reprocessing after a delay
                redis_client.zadd("scheduled", {task: datetime.now().timestamp() + 60})
                redis_client.delete(request_key)
    except Exception as e:
        logger.error(f"Error processing task: {e}")

def create_task_and_context(data):
    task_type = data["type"]
    if task_type == "RESPOND":
        context = MessageContextManager(config, data["original_request"])
        task = RespondTask(context.message)
    elif task_type == "REMIND":
        context = CronContextManager(config, data["room_id"])
        task = RemindTask()
    elif task_type == "REVIVE":
        context = None
        task = ReviveTask()
    else:
        logger.warning(f"Unknown task type: {task_type}")
        return None, None
    return context, task
