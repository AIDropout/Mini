import json
from datetime import datetime

from mini.core.logger import get_logger
from mini.server.celery import celery_app
from mini.server.redis import RedisManager

logger = get_logger(__name__)


class CancelManager:
    def __init__(self, redis_manager: RedisManager):
        self.redis_manager = redis_manager

    def newer_message_found(self, room_id: str, current_task_id: str) -> bool:
        pattern = f"{room_id}:*"
        current_task_time = None
        newer_message_found = False

        # First, get the current task's created_at time
        current_key = f"{room_id}:{current_task_id}"
        current_task_data = json.loads(self.redis_manager.get(current_key))
        current_task_time = datetime.fromisoformat(current_task_data["created_at"])

        # Now compare with all other tasks
        for key in self.redis_manager.scan_iter(match=pattern):
            _, task_id = key.split(":", 1)
            if task_id == current_task_id:
                continue  # Skip the current task

            task_data = json.loads(self.redis_manager.get(key))
            task_time = datetime.fromisoformat(task_data["created_at"])

            if task_time > current_task_time:
                newer_message_found = True
                logger.info(
                    f"🍊 Found newer task for room id {room_id}. Current task should be cancelled."
                )
                break

        if not newer_message_found:
            logger.info(
                f"No newer tasks found for room id {room_id}. Current task can continue."
            )

        return newer_message_found

    def remove_task(self, room_id: str, task_id: str) -> None:
        """
        Cancel a specific task for a given room.

        Args:
            room_id (str): The ID of the room for which to cancel the task.
            task_id (str): The ID of the task to cancel.
        """
        key = f"{room_id}:{task_id}"
        celery_app.control.revoke(task_id, terminate=True, signal="SIGKILL")
        self.redis_manager.delete(key)
        logger.info(f"🍊 Removed task {task_id} for room id {room_id}.")