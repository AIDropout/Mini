# services/room_service.py
from fastapi import BackgroundTasks
from zootopia.manager.database import DatabaseManager
from zootopia.manager.messaging import MessagingManager
from zootopia.core.schema import Tables, Message, Room, User
from zootopia.utils.time_utils import should_send_proactive_message
from zootopia.controller.tasks.task_scheduler import TaskScheduler
from zootopia.controller.tasks.task_types import ReviveTask, ScheduledTaskInfo
from zootopia.core.error import error_handler


class CronService:
    def __init__(
        self, database_manager: DatabaseManager, messaging_manager: MessagingManager
    ):
        self.database_manager = database_manager
        self.messaging_manager = messaging_manager

    @error_handler("CronService")
    async def refresh_rooms(
        self, background_tasks: BackgroundTasks, dev_mode: bool = False
    ):
        agents = self.database_manager.query(
            Tables.AGENTS.value, ("id", "=", 1) if dev_mode else None
        )

        for agent in agents:
            proactive_rooms = self.database_manager.query(
                Tables.ROOMS.value,
                (Tables.ROOMS__agent_id.value, agent.id),
                (Tables.ROOMS__agent_proactivity.value, ">", 0),
            )

            for room in proactive_rooms:
                if self._is_room_eligible_for_revival(room, room.user_id):
                    last_message = self.database_manager.get_row(
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
                            db=self.database_manager,
                        )

    async def _is_room_eligible_for_revival(self, room: Room, user_id: int):
        if not room.subscribe_msg_sent:
            return True

        active_subscription = self.database_manager.get_row(
            Tables.SUBSCRIPTIONS.value,
            {
                Tables.SUBSCRIPTIONS__user_id.value: user_id,
                Tables.SUBSCRIPTIONS__status.value: "active",
            },
        )

        return active_subscription is not None
