from mini.core.logger import get_logger
from mini.server.celery import celery_app
from mini.server.redis import RedisManager

logger = get_logger(__name__)


class CancelManager:
    def __init__(self, redis_manager: RedisManager):
        self.redis_manager = redis_manager

    def cancel_existing_task(self, room_id: str) -> bool:
        """
        Cancel an existing scheduled task for a given room.

        Args:
            room_id (str): The ID of the room for which to cancel the task.

        Returns:
            bool: True if a task was cancelled, False otherwise.
        """

        pattern = f"{room_id}:*"
        tasks_cancelled = False

        for key in self.redis_manager.scan_iter(match=pattern):
            # Extract the task_id from the key
            _, task_id = key.split(":", 1)

            # Cancel the existing task
            celery_app.control.revoke(task_id, terminate=True, signal="SIGKILL")
            self.redis_manager.delete(key)
            logger.info(f"🍊 Canceled task {task_id} for room id {room_id}.")
            tasks_cancelled = True

        if not tasks_cancelled:
            logger.info(f"No tasks found for room id {room_id}.")

        return tasks_cancelled
