from zootopia.manager.database import DatabaseManager
from zootopia.manager.messaging import MessagingManager
from zootopia.core.schema import Message, Tables
from zootopia.utils.time_utils import calculate_response_delay
from zootopia.core.error import error_handler
from zootopia.controller.tasks.task_scheduler import TaskScheduler
from zootopia.controller.tasks.task_types import ScheduledTaskInfo, RespondTask

class MessageService:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.messaging_manager = MessagingManager()

    @error_handler("HandleRespond")
    async def handle_respond(self, request_body: dict):
        context = await self.messaging_manager.create_message_context(request_body)
        
        inserted_message = await self.db_manager.insert(
            Tables.MESSAGES.value,
            Message(
                room_id=context.room.id,
                sender_id=context.user.id,
                content=context.message.content,
            ),
        )

        recent_messages = await self.db_manager.get_multiple_rows(
            Tables.MESSAGES.value,
            max_rows=5,
            order_by="created_at",
            order_desc=True,
            conditions={"room_id": context.room.id},
        )
        delay = calculate_response_delay(recent_messages)

        scheduled_task_info = ScheduledTaskInfo(
            task=RespondTask(user_message=context.message, room_id=context.room.id),
            delay=delay,
            original_request=request_body,
        )

        await TaskScheduler.schedule_task(
            task_data=scheduled_task_info.to_dict(),
            delay=delay,
            db=self.db_manager,
        )