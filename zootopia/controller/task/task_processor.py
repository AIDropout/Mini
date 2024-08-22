from celery import shared_task
from config.container import container
from zootopia.server.cancel import cancel_existing_task
from zootopia.core.schema.task import TaskType
from zootopia.controller.task.task_types import RemindTask, ReviveTask, RespondTask
from zootopia.core.logger import get_logger
from datetime import datetime
import asyncio

logger = get_logger(__name__)


@shared_task(bind=True, max_retries=2)
def process_task(self, data: dict):
    logger.info(f"🔴🔴🔴 running at {datetime.now()}")
    messaging_manager_factory = container.get_messaging_manager_factory()
    messaging_manager = None
    context_factory = container.get_context_factory()
    context = None
    task = None

    request = data["original_request"]
    task_type = data["type"]
    room_id = data["room_id"]

    try:

        if task_type == TaskType.RESPOND:
            messaging_manager = messaging_manager_factory.get_manager_from_request(
                request
            )
            message = messaging_manager.receive_message(request)
            context = context_factory.create_message_context(message)
            task = RespondTask(user_message=message, room_id=room_id)
        elif task_type == TaskType.REVIVE:
            context = context_factory.create_cron_context(room_id)
            messaging_manager = messaging_manager_factory._bird_manager
            task = ReviveTask(room_id)
        elif task_type == TaskType.REMIND:
            context = context_factory.create_cron_context(room_id)
            messaging_manager = messaging_manager_factory._bird_manager
            task = RemindTask()
        else:
            raise NotImplementedError(f"Unknown task type {task_type}")

        if not task:
            logger.warning(f"Invalid task data: {data}")
            return

        agent = container.get_agent_service()

        agent.configure(
            messaging_manager=messaging_manager,
            agent=context.agent,
            user=context.user,
            room=context.room,
        )

        success = asyncio.run(agent.handle_chat_task(task))

        if success:
            cancel_existing_task(room_id)

    except Exception as exc:
        logger.error(f"Error processing task: {exc}")
        self.retry(exc=exc, countdown=60)
