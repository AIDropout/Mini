from zootopia.core.logger import logger
from zootopia.controller.context import MessageContextManager
from zootopia.core.schema import (
    MessageTableModel,
    Tables,
)
from zootopia.controller.tasks.task_scheduler import TaskScheduler
from zootopia.controller.tasks.task_types import ScheduledTaskInfo, RespondTask
from zootopia.utils.time_utils import calculate_response_delay


def handle_respond(request_body: dict):
    """
    Called by /message endpoint.
    This function inserts the user message and
    schedules the task based on a calculated delay
    """

    try:
        context = MessageContextManager(request_body)

        """Insert the user message"""
        inserted_message = context.database.insert(
            Tables.MESSAGES.value,
            MessageTableModel(
                room_id=context.room.id,
                sender_id=context.user.id,
                content=context.message.content,
            ),
        )

        """Calculate delay of response"""
        recent_messages = context.database.get_multiple_rows(
            Tables.MESSAGES.value,
            max_rows=5,
            order_by="created_at",
            order_desc=True,
            conditions={"room_id": context.room.id},
        )
        delay = calculate_response_delay(recent_messages)

        """Formulate and schedule response as a task"""
        scheduled_task_info = ScheduledTaskInfo(
            task=RespondTask(user_message=context.message, room_id=context.room.id),
            delay=delay,
            original_request=request_body,
        )

        TaskScheduler.schedule_task(
            task_data=scheduled_task_info.to_dict(), delay=delay, db=context.database
        )

    except Exception as e:
        logger.exception(f"Exception in schedule respond: {e}")
