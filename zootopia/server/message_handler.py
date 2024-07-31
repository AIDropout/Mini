import random
from typing import List
from datetime import datetime, timedelta

from zootopia.core.config import config
from zootopia.core.logger import logger
from zootopia.controller.context import MessageContextManager
from zootopia.core.schema import (
    MessageTableModel,
    Tables,
    TaskType,
)

from zootopia.server.celery.tasks import process_task
from zootopia.server.redis.redis import redis_manager
from zootopia.server.cancel import cancel_existing_task


def handle_message(request_body: dict):
    """This is called by /message endpoint.

    1. Inserts the user message
    2. Cancels any existing scheduled tasks for this room
    3. Calculates a response time, and schedules a new celery task.
    """
    try:
        context = MessageContextManager(request_body)
        room_id = context.room.id
        incoming_message = context.message.content

        # Insert the user message
        context.database.insert(
            Tables.MESSAGES.value,
            MessageTableModel(
                room_id=room_id,
                from_user=True,
                content=incoming_message,
            ),
        )

        recent_messages = context.database.get_multiple_rows(
            Tables.MESSAGES.value,
            max_rows=5,
            order_by="created_at",
            order_desc=True,
            conditions={"room_id": room_id},
        )

        delay = calculate_response_delay(recent_messages)
        creation_time = datetime.now()
        response_time = datetime.now() + timedelta(seconds=delay)

        # Revoke previous tasks if any
        cancel_existing_task(room_id)

        # Schedule the task for Celery
        task_data = {
            "type": TaskType.RESPOND.value,
            "response_time": response_time.isoformat(),
            "creation_time": creation_time.isoformat(),
            "original_request": request_body,
            "room_id": room_id,
            "message": incoming_message,
        }
        new_task = process_task.apply_async(args=[task_data], countdown=delay)
        logger.info(
            f"🟢 Scheduled bot response in {delay} seconds"
            f"🟢 Current time: {datetime.now().isoformat()}"
            f"🟢 Scheduled response time: {response_time.isoformat()}"
        )

        # Store the new task ID in Redis
        redis_manager.set_scheduled_task(room_id, new_task.id, delay + 60)

    except Exception as e:
        logger.exception(f"Exception in schedule respond: {e}")

def calculate_response_delay(messages: List[dict]) -> int:
    if len(messages) < 2:
        return 5  # Default delay if not enough messages

    # Calculate average time between messages
    time_diffs = []
    for i in range(1, len(messages)):
        try:
            time1 = datetime.fromisoformat(
                messages[i - 1]["created_at"].replace("Z", "+00:00")
            )
            time2 = datetime.fromisoformat(
                messages[i]["created_at"].replace("Z", "+00:00")
            )
            time_diff = (time1 - time2).total_seconds()
            time_diffs.append(time_diff)
        except (ValueError, KeyError) as e:
            logger.warning(f"Error parsing datetime: {e}")
            continue

    if not time_diffs:
        return 5  # Default delay if we couldn't calculate any time differences

    avg_time_between_messages = sum(time_diffs) / len(time_diffs)

    # Adjust delay based on message frequency
    if avg_time_between_messages < 5:
        return 10  # Longer delay for rapid messages
    elif avg_time_between_messages < 30:
        return 5
    else:
        return 3  # Quicker response for infrequent messages
