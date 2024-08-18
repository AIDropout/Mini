from zootopia.core.logger import logger
from zootopia.controller.task.task_processor import process_task
from zootopia.server.redis.redis import redis_manager
from zootopia.server.cancel import cancel_existing_task
from zootopia.manager.database import DatabaseManager
from zootopia.core.schema import TaskType, Schedule
from datetime import datetime, timedelta
from typing import Optional
from zootopia.service.base import Service


class SchedulerService(Service):
    def __init__(self, database_manager: DatabaseManager):
        super().__init__(database_manager)

    def schedule_task(
        self, task_data: dict, delay: int = 0, db: Optional[DatabaseManager] = None
    ):
        """
        Schedule a task, choosing between short-term and long-term based on the delay
        If delay > 1 hour, schedule as a long-term task
        """
        room_id = task_data["room_id"]
        if delay <= 3600:  # 1 hour in seconds
            if room_id:
                cancel_existing_task(room_id)

            new_task = process_task.apply_async(args=[task_data], countdown=delay)
            logger.info(
                f"🟢 Scheduled short-term task in {delay} seconds"
                f"🟢 Current time: {datetime.now().isoformat()}"
                f"🟢 Scheduled response time: {(datetime.now() + timedelta(seconds=delay)).isoformat()}"
            )

            redis_manager.set_scheduled_task(room_id, new_task.id, delay + 60)

        else:
            # Handle long schedule
            raise NotImplementedError
