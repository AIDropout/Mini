from zootopia.server.celery import celery_app
from zootopia.server.redis.redis import redis_manager
from zootopia.core.logger import logger


def cancel_existing_task(room_id: str) -> bool:
    """
    Cancel an existing scheduled task for a given room.

    Args:
        room_id (str): The ID of the room for which to cancel the task.

    Returns:
        bool: True if a task was cancelled, False otherwise.
    """
    existing_task_id = redis_manager.get_scheduled_task(room_id)

    if existing_task_id:
        # Cancel the existing task
        celery_app.control.revoke(
            existing_task_id.decode(), terminate=True, signal="SIGKILL"
        )
        redis_manager.delete_scheduled_task(room_id)
        logger.info(f"🍊 Canceled previous task for room id {room_id}.")
        return True

    return False
