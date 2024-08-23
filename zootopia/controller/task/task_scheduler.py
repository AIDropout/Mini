from zootopia.core.logger import logger
from zootopia.controller.task.task_processor import process_task
from zootopia.controller.task.task_types import RespondTask, TaskType
from zootopia.server.cancel import cancel_existing_task
from zootopia.manager.database import DatabaseManager
from datetime import datetime, timedelta
from typing import Optional
from zootopia.service.base import Service
from zootopia.core.schema.message import ZootopiaMessage
from zootopia.service.context_factory import Context
from zootopia.server.redis import RedisManager
from uuid import uuid4


class SchedulerService(Service):
    def __init__(self, database_manager: DatabaseManager, redis_manager: RedisManager):
        super().__init__(database_manager)
        self.redis_manager = redis_manager

    def schedule_respond(self, delay: int, message: ZootopiaMessage, context: Context):
        """Constructs task object, stores it in Redis, and schedules a Celery short-term task"""

        scheduled_time = datetime.now() + timedelta(seconds=delay)
        room_id = context.room.id

        task = RespondTask(
            id=str(uuid4()),
            scheduled_for=scheduled_time,
            user_message=message,
            context=context,
        )

        if delay <= 3600:
            cancel_existing_task(room_id)

            new_task = process_task.apply_async(
                args=[room_id, task.id, TaskType.RESPOND], countdown=delay
            )
            logger.info(
                f"🟢 Scheduled short-term task in {delay} seconds\n"
                f"🟢 Current time: {datetime.now().isoformat()}\n"
                f"🟢 Scheduled response time: {task.scheduled_for.isoformat()}"
                f"🟢 Test: {new_task}"
            )

            if new_task:
                # Store full task data in Redis
                self.redis_manager.set(
                    key=f"{room_id}:{task.id}",
                    value=task.model_dump_json(),
                    expiry=delay + 120,
                )

        else:
            pass  # Handle long term tasks
