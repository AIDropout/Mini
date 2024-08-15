from celery import shared_task
from zootopia.service.context import ContextFactory, CronContextService
from zootopia.manager.messaging import MessagingManagerFactory
from zootopia.core.schema import TaskType
from zootopia.controller.agent.agent import Agent
from zootopia.controller.tasks.task_types import RemindTask, ReviveTask, RespondTask
from zootopia.core.logger import get_logger
import asyncio
from datetime import datetime
from zootopia.server.cancel import cancel_existing_task

logger = get_logger(__name__)


@shared_task(bind=True, max_retries=2)
def process_task(self, data: dict):
    logger.info(f"🔴🔴🔴 running at {datetime.now()}")
    messaging_manager_factory = MessagingManagerFactory()
    context_factory = ContextFactory(messaging_manager_factory)

    try:
        context = None
        task = None

        task_type = data["type"]
        if task_type == TaskType.RESPOND.value:
            context = context_factory.create_message_context(
                request_body=data["original_request"]
            )
            task = RespondTask(user_message=context.message, room_id=data["room_id"])
        elif task_type == TaskType.REMIND.value:
            context = CronContextService(data["room_id"])
            task = RemindTask()
        elif task_type == TaskType.REVIVE.value:
            context = CronContextService(data["room_id"])
            task = ReviveTask(room_id=data["room_id"])
        else:
            logger.warning(f"Unknown task type: {task_type}")
            return

        if not context or not task:
            logger.warning(f"Invalid task data: {data}")
            return

        agent = Agent(context)
        success = asyncio.run(agent.handle_chat_task(task))

        cancel_existing_task(context.room.id)

    except Exception as exc:
        logger.error(f"Error processing task: {exc}")
        self.retry(exc=exc, countdown=60)
