from celery import Task
from celery.exceptions import Ignore as Canceled
from typing import Optional, List

from mini.core.logger import get_logger
from mini.server.redis.redis import RedisManager

logger = get_logger(__name__)

# TODO: in future, have new tasks retroactively cancel prior tasks
class CancellableTask(Task):
    _redis_manager = None

    @classmethod
    def init_redis(cls, redis_manager: RedisManager) -> None:
        cls._redis_manager = redis_manager

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.room_id: Optional[str] = None

    @classmethod
    def register_task(cls, room_id: str, task_id: str) -> None:
        """
        Adds the given task's id to the front of the list of tasks for the room. 
        Called in MessagingService.
        """
        if not room_id:
            raise ValueError("room_id is required for cancellable task.")
        logger.info(f"1️⃣ Registering new task {task_id} for room {room_id}")
        cls._redis_manager.lpush(f"tasks:{room_id}", task_id)
        # Optionally, limit the number of stored tasks (e.g., keep only the most recently added 5)
        cls._redis_manager.ltrim(f"tasks:{room_id}", 0, 5)

    def check_cancellation(self) -> None:
        """
        Checks if current task id is the most recent task for the room.
        - If it isn't, cancel the task.
        - Called intermittently in celery task
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