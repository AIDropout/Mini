from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from mini.controller.task.task_processor import process_task
from mini.controller.task.task_types import RespondTask, TaskType
from mini.core.logger import get_logger
from mini.core.schema.message import MiniMessage
from mini.manager.database import DatabaseManager
from mini.server.cancel import CancelManager
from mini.server.redis import RedisManager
from mini.service.base import Service
from mini.service.context_factory import Context

logger = get_logger(__name__)


class SchedulerService(Service):
    def __init__(
        self,
        database_manager: DatabaseManager,
        redis_manager: RedisManager,
        cancel_manager: CancelManager,
    ):
        super().__init__(database_manager)
        self.redis_manager = redis_manager
        self.cancel_manager = cancel_manager

    def schedule_respond(self, delay: int, message: MiniMessage, context: Context):
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

            if self.cancel_manager.newer_task_found(room_id, task.id):
                return

            new_task = process_task.apply_async(
                args=[room_id, task.id, TaskType.RESPOND], countdown=delay
            )

            if new_task:
                # Store full task data in Redis
                self.redis_manager.set(
                    key=f"{room_id}:{task.id}",
                    value=task.model_dump_json(),
                    expiry=delay + 120,
                )

                logger.info(
                    f"🟢 Scheduled short-term task in {delay} seconds\n"
                    f"🟢 Current time: {datetime.now().isoformat()}\n"
                    f"🟢 Scheduled response time: {task.scheduled_for.isoformat()}"
                )
        else:
            pass  # Handle long term tasks
