from celery import shared_task
from zootopia.controller.context import MessageContextManager, CronContextManager
from zootopia.core.schema import TaskType
from zootopia.controller.agent.agent import Agent
from zootopia.controller.tasks.task_types import RemindTask, ReviveTask, RespondTask
from zootopia.core.logger import logger
import asyncio
from datetime import datetime
from zootopia.server.cancel import cancel_existing_task


@shared_task(bind=True, max_retries=2)
def process_task(self, data: dict):
    logger.info(f"🔴🔴🔴 running at {datetime.now()}")
    try:
        context, task = create_task_and_context(data)
        if not context or not task:
            logger.warning(f"Invalid task data: {data}")
            return

        agent = Agent.from_context(context)
        success = asyncio.run(agent.handle_chat_task(task))

        if not success:
            cancel_existing_task(context.room.id)
        else:
            raise Exception("Task processing failed")
    except Exception as exc:
        logger.error(f"Error processing task: {exc}")
        self.retry(exc=exc, countdown=60)


def create_task_and_context(data: dict):
    task_type = data["type"]
    if task_type == TaskType.RESPOND.value:
        context = MessageContextManager(data["original_request"])
        task = RespondTask(context.message)
    elif task_type == TaskType.REMIND.value:
        context = CronContextManager(data["room_id"])
        task = RemindTask()
    elif task_type == TaskType.REVIVE.value:
        context = None
        task = ReviveTask()
    else:
        logger.warning(f"Unknown task type: {task_type}")
        return None, None
    return context, task
