# services/room_service.py
from fastapi import BackgroundTasks
from zootopia.manager.database import DatabaseManager
from zootopia.manager.messaging import MessagingManager
from zootopia.core.schema import Tables, Message
from zootopia.utils.time_utils import should_send_proactive_message
from zootopia.controller.tasks.task_scheduler import TaskScheduler
from zootopia.controller.tasks.task_types import ReviveTask, ScheduledTaskInfo
from zootopia.core.error import error_handler


class RoomService:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.messaging_manager = MessagingManager()

    @error_handler("HandleRevive")
    async def handle_revive(
        self, background_tasks: BackgroundTasks, dev_mode: bool = False
    ):
        agents = self.db_manager.query(Tables.AGENTS.value, ("id", "=", 1) if dev_mode else None)


        for agent in agents:
            proactive_rooms = await self.db_manager.query(
                Tables.ROOMS.value,
                (Tables.ROOMS__agent_id.value, agent.id),
                (Tables.ROOMS__agent_proactivity.value, ">", 0),
            )

            for room in proactive_rooms:
                if await self._is_room_eligible_for_revival(room):
                    last_message = await self.db_manager.get_row(
                        Tables.MESSAGES.value,
                        {Tables.MESSAGES__room_id.value: room.id},
                        order_by=Tables.MESSAGES__created_at.value,
                        order_desc=True,
                    )

                    if last_message and should_send_proactive_message(
                        agent_proactivity=room.agent_proactivity,
                        last_message_time=last_message.created_at,
                    ):
                        revive_task = ReviveTask(room_id=room.id)
                        scheduled_task_info = ScheduledTaskInfo(
                            task=revive_task, delay=0
                        )

                        await TaskScheduler.schedule_task(
                            task_data=scheduled_task_info.to_dict(),
                            delay=0,
                            db=self.db_manager,
                        )

    async def _is_room_eligible_for_revival(self, room):
        if not room.subscribe_msg_sent:
            return True

        active_subscription = await self.db_manager.get_row(
            Tables.SUBSCRIPTIONS.value,
            {
                Tables.SUBSCRIPTIONS__room_id.value: room.id,
                Tables.SUBSCRIPTIONS__ended_at.value: None,
            },
        )

        return active_subscription is not None

    async def send_admin_message(self, payload: dict):
        room_id = payload.get("room_id")
        message = payload.get("message")

        if not room_id or not message:
            raise ValueError("Missing room_id or message")

        context = await self.messaging_manager.create_cron_context(room_id)

        new_message = Message(
            sender_id=context.room.agent_id,
            room_id=room_id,
            content=message,
            sent_by_admin=True,
        )

        await self.db_manager.insert(Tables.MESSAGES.value, new_message)
        await context.messaging_manager.send_message(message)
