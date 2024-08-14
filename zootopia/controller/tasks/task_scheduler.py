from zootopia.core.logger import logger
from zootopia.controller.tasks.task_processor import process_task
from zootopia.server.redis.redis import redis_manager
from zootopia.server.cancel import cancel_existing_task
from zootopia.service import Database
from zootopia.core.schema import TaskType, Schedule
from datetime import datetime, timedelta
from typing import Optional


class TaskScheduler:
    def __init__(self, db: Database):
        self.db = db

    @staticmethod
    def schedule_task(task_data: dict, delay: int = 0, db: Optional[Database] = None):
        """
        TODO: DEBUG
        Schedule a task, choosing between short-term and long-term based on the delay
        If delay > 1 hour, schedule as a long-term task
        """
        if delay <= 3600:  # 1 hour in seconds
            TaskScheduler(db).schedule_short_term_task(task_data, delay)
        else:
            if not db:
                raise ValueError(
                    "Supabase connection required for long-term task scheduling"
                )

            run_at = datetime.now() + timedelta(seconds=delay)
            TaskScheduler(db).schedule_long_term_task(
                task_type=TaskType(task_data["type"]),
                room_id=task_data["room_id"],
                run_at=run_at,
                info=str(task_data),
            )

    def schedule_short_term_task(self, task_data: dict, delay: int = 0):
        """Schedule a short-term task using Celery and Redis"""
        room_id = task_data.get("room_id")
        if room_id:
            cancel_existing_task(room_id)

        new_task = process_task.apply_async(args=[task_data], countdown=delay)
        logger.info(
            f"🟢 Scheduled short-term task in {delay} seconds"
            f"🟢 Current time: {datetime.now().isoformat()}"
            f"🟢 Scheduled response time: {(datetime.now() + timedelta(seconds=delay)).isoformat()}"
        )

        if room_id:
            redis_manager.set_scheduled_task(room_id, new_task.id, delay + 60)

    def schedule_long_term_task(
        self,
        task_type: TaskType,
        room_id: int,
        run_at: datetime,
        info: Optional[str] = None,
    ):
        """TODO: Full implementation
        Schedule a long-term task using Supabase, called by Cron later"""
        model = Schedule(
            room_id=room_id,
            run_at=run_at,
            type=task_type,
        )

        if info:
            model.info = info

        self.db.insert(Schedule.table_name(), model.dict())
        logger.info(
            f"🟢 Scheduled long-term task"
            f"🟢 Task type: {task_type}"
            f"🟢 Room ID: {room_id}"
            f"🟢 Run at: {run_at.isoformat()}"
        )
