from celery import shared_task
from config.container import container
from zootopia.server.cancel import cancel_existing_task
from zootopia.core.schema.task import TaskType
from zootopia.controller.task.task_types import RemindTask, ReviveTask, RespondTask
from zootopia.core.logger import get_logger
from datetime import datetime
import asyncio
from typing import Literal

logger = get_logger(__name__)


@shared_task(bind=True, max_retries=2)
def process_task(
    self,
    room_id: str,
    task_id: str,
    task_type: Literal[TaskType.REMIND, TaskType.RESPOND, TaskType.REVIVE],
):
    try:
        logger.info(f"🔴🔴🔴 running at {datetime.now()}")
        redis_manager = container.get_redis_manager()
        messaging_manager_factory = container.get_messaging_manager_factory()
        messaging_manager = messaging_manager_factory.bird_manager

        task_json = redis_manager.get(f"{room_id}:{task_id}")
        if not task_json:
            logger.error(f"Task {task_id} in room {room_id} not found in Redis")
            return

        task: RespondTask = None

        if task_type == TaskType.RESPOND:
            task = RespondTask.model_validate_json(task_json)
        elif task_type == TaskType.REMIND:
            pass
        elif task_type == TaskType.REVIVE:
            pass

        if not task or not messaging_manager:
            logger.error(
                f"Failed to initialize task or messaging manager for task {task_id}"
            )
            return

        messaging_manager.set_receiver(task.context.user.phone_number)
        messaging_manager.set_sender(task.context.agent.bird_channel_id)

        agent = container.get_agent_controller()

        agent.configure(
            messaging_manager=messaging_manager,
            agent=task.context.agent,
            user=task.context.user,
            room=task.context.room,
        )

        success = asyncio.run(agent.handle_chat_task(task))

        if success:
            cancel_existing_task(room_id)

        redis_manager.delete(f"task:{task_id}")

    except Exception as e:
        logger.exception(f"Error processing task {task_id}: {str(e)}")
        raise self.retry(exc=e)
