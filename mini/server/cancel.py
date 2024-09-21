import json
from datetime import datetime

from mini.core.logger import get_logger
from mini.server.celery import celery_app
from mini.server.redis import RedisManager

logger = get_logger(__name__)


class CancelManager:
    def __init__(self, redis_manager: RedisManager):
        self.redis_manager = redis_manager

    def newer_task_found(self, room_id: str, current_task_id: str) -> bool:
        pattern = f"{room_id}:*"
        current_task_time = None
        newer_task_found = False

        for key in self.redis_manager.scan_iter(match=pattern):
            _, task_id = key.split(":", 1)
            task_data = json.loads(self.redis_manager.get(key))
            task_time = datetime.fromisoformat(task_data['created_at'])

            if task_id == current_task_id:
                current_task_time = task_time
            elif current_task_time is None or task_time > current_task_time:
                newer_task_found = True
                logger.info(f"🍊 Removing current task {current_task_id} for room id {room_id} due to newer task {task_id}...")
                self.remove_task(room_id, current_task_id)
                break

        if not newer_task_found:
            logger.info(f"No newer tasks found for room id {room_id}. Current task {current_task_id} can continue.")

        return newer_task_found

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
