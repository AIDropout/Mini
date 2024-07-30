from celery import shared_task
from zootopia.context import MessageContextManager, CronContextManager
from zootopia.core.schema import RespondTask, RemindTask, ReviveTask, TaskType
from zootopia.agent.agent import Agent
from config.config import config
from zootopia.core.logger import logger
import json
import asyncio


@shared_task(bind=True, max_retries=3)
def process_task(self, data: dict):
    try:
        # If data is bytes, decode it to a dictionary
        if isinstance(data, bytes):
            data = json.loads(data.decode("utf-8"))
        elif not isinstance(data, dict):
            raise ValueError(f"Expected dict or bytes, got {type(data)}")

        context, task = create_task_and_context(data)
        if task is None or context is None:
            logger.warning(f"Invalid task data: {data}")
            return

        agent = Agent.from_config(config, context)
        success = asyncio.run(agent.handle_chat_task(task))

        if not success:
            raise Exception("Task processing failed")
    except Exception as exc:
        logger.error(f"Error processing task: {exc}")
        self.retry(exc=exc, countdown=60)


def create_task_and_context(data: dict):
    task_type = data["type"]
    if task_type == TaskType.RESPOND.value:
        context = MessageContextManager(config, data["original_request"])
        task = RespondTask(context.message)
    elif task_type == TaskType.REMIND.value:
        context = CronContextManager(config, data["room_id"])
        task = RemindTask()
    elif task_type == TaskType.REVIVE.value:
        context = None
        task = ReviveTask()
    else:
        logger.warning(f"Unknown task type: {task_type}")
        return None, None
    return context, task
