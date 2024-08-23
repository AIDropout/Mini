from zootopia.server.celery import celery_app
from config.container import container
from zootopia.core.logger import get_logger

logger = get_logger(__name__)


def cancel_existing_task(room_id: str) -> bool:
    """
    Cancel an existing scheduled task for a given room.

    Args:
        room_id (str): The ID of the room for which to cancel the task.

    Returns:
        bool: True if a task was cancelled, False otherwise.
    """
    redis_manager = container.get_redis_manager()

    pattern = f"{room_id}:*"
    tasks_cancelled = False

    for key in redis_manager.scan_iter(match=pattern):
        # Extract the task_id from the key
        _, task_id = key.split(":", 1)

        # Cancel the existing task
        celery_app.control.revoke(task_id, terminate=True, signal="SIGKILL")
        redis_manager.delete(key)
        logger.info(f"🍊 Canceled task {task_id} for room id {room_id}.")
        tasks_cancelled = True

    if not tasks_cancelled:
        logger.info(f"No tasks found for room id {room_id}.")

    return tasks_cancelled
