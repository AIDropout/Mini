from celery import Task
from celery.exceptions import Ignore as Canceled
from typing import Optional, List

from mini.core.logger import get_logger
from mini.server.redis.redis import RedisManager

logger = get_logger(__name__)

class CancellableTask(Task):
    _redis_manager = None

    @classmethod
    def init_redis(cls, redis_manager: RedisManager) -> None:
        cls._redis_manager = redis_manager

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.room_id: Optional[str] = None

    def register_task(self, room_id: str) -> None:
        """
        Adds the current task's id to the front of the list of tasks for the room.
        """
        if not room_id:
            raise ValueError("room_id is required for cancellable task.")
        self.room_id = room_id
        logger.info(f"1️⃣ Registering new task {self.request.id} for room {room_id}")
        self._redis_manager.lpush(f"tasks:{room_id}", self.request.id)
        # Optionally, limit the number of stored tasks (e.g., keep only the most recently added 5)
        self._redis_manager.ltrim(f"tasks:{room_id}", 0, 5)

    def check_cancellation(self) -> None:
        """
        Checks if current task id is the most recent task for the room.
        - If it isn't, cancel the task.
        """
        if self.room_id is None:
            raise ValueError("Task not properly initialized. Call register_task first.")
        latest_task_id = self._redis_manager.lindex(f"tasks:{self.room_id}", 0)
        if latest_task_id:
            latest_task_id = latest_task_id.decode('utf-8')
        logger.info(
            f"🟢 latest task id: {latest_task_id} \n current task_id: {self.request.id}"
        )
        if latest_task_id is not None and latest_task_id != self.request.id:
            logger.warning(f"🔴🔴🔴Task {self.request.id} was cancelled.🔴🔴🔴")
            raise Canceled()

    def __call__(self, *args, **kwargs):
        """
        Runs cleanup method at end of the func.
        """
        try:
            return super().__call__(*args, **kwargs)
        finally:
            self.delete_task_key()

    def delete_task_key(self) -> None:
        """
        Removes the current task ID from the list in Redis.
        """
        if self.room_id:
            removed = self._redis_manager.lrem(f"tasks:{self.room_id}", 0, self.request.id)
            logger.info(f"Removed {removed} occurrence(s) of task {self.request.id} from room {self.room_id}")