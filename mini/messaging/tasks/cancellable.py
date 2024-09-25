from celery import Task
from celery.exceptions import Ignore as Canceled
from typing import Optional

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
        Sets the current task's id as the latest task.
        """
        if not room_id:
            raise ValueError("room_id is required for cancellable task.")
        self.room_id = room_id
        logger.info(f"1️⃣ Registering new latest task {self.request.id}")
        self._redis_manager.set(f"latest_task:{room_id}", self.request.id)

    def should_cancel(self) -> bool:
        """
        Checks if current task id matches the latest task id.
        """
        if self.room_id is None:
            raise ValueError("Task not properly initialized. Call register_task first.")
        latest_task_id = self._redis_manager.get(f"latest_task:{self.room_id}")
        
        # Decode the bytes to string if it's not None
        if latest_task_id is not None:
            latest_task_id = latest_task_id.decode('utf-8')
        
        logger.info(
            f"🟢 latest task id: {latest_task_id} \n current task_id: {self.request.id}"
        )
        return latest_task_id is not None and latest_task_id != self.request.id

    def check_cancellation(self) -> None:
        """
        Cancels a task if it needs to be canceled.
        """
        if self.should_cancel():
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
        Deletes the task's key from Redis.
        """
        if self.room_id:
            self._redis_manager.delete(f"latest_task:{self.room_id}")