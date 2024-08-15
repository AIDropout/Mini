from zootopia.manager.database import DatabaseManager
from zootopia.manager.messaging import MessagingManagerFactory
from zootopia.core.schema import Message, Tables
from zootopia.utils.time_utils import calculate_response_delay
from zootopia.core.error import error_handler
from zootopia.controller.tasks.task_scheduler import TaskScheduler
from zootopia.controller.tasks.task_types import ScheduledTaskInfo, RespondTask
from zootopia.service.context import ContextFactory


class ReplyService:
    def __init__(
        self,
        database_manager: DatabaseManager,
        context_factory: ContextFactory,
        messaging_manager_factory: MessagingManagerFactory,
    ):
        self.database_manager = database_manager
        self.context_factory = context_factory
        self.messaging_manager_factory = messaging_manager_factory

    @error_handler("ReplyService")
    def handle_respond(self, request_body: dict):
        context = self.context_factory.create_message_context(request_body)
        messaging_manager = self.messaging_manager_factory.get_manager_from_request(
            request_body
        )

        inserted_message = self.database_manager.insert(
            Tables.MESSAGES.value,
            Message(
                room_id=context.room.id,
                sender_id=context.user.id,
                content=context.message.content,
            ),
        )

        recent_messages = self.database_manager.get_multiple_rows(
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

        TaskScheduler.schedule_task(
            task_data=scheduled_task_info.to_dict(),
            delay=delay,
            db=self.database_manager,
        )

    # Define the Request
    async def send_admin_message(self, payload: dict):
        room_id = payload.get("room_id")
        message = payload.get("message")

        if not room_id or not message:
            raise ValueError("Missing room_id or message")

        context = self.context_factory.create_cron_context(room_id)

        new_message = Message(
            sender_id=context.room.agent_id,
            room_id=room_id,
            content=message,
            sent_by_admin=True,
        )

        self.database_manager.insert(Tables.MESSAGES.value, new_message)
        bird_manager = self.messaging_manager_factory.bird_manager
        await bird_manager.send_message(message)
