# services/room_service.py
from fastapi import BackgroundTasks
from zootopia.manager.database import DatabaseManager
from zootopia.manager.messaging import MessagingManager
from zootopia.core.schema.tables import Tables, Message, Room, User
from zootopia.controller.task.task_scheduler import SchedulerService
from zootopia.controller.task.task_types import ReviveTask
from zootopia.core.error import error_handler
from zootopia.service.base import Service
from datetime import datetime, timedelta, timezone
import random
from zootopia.core.schema.subscription import SubscriptionStatus


class CronService(Service):
    def __init__(
        self, database_manager: DatabaseManager, messaging_manager: MessagingManager
    ):
        super().__init__(database_manager)
        self.messaging_manager = messaging_manager

    @error_handler("CronService")
    async def refresh_rooms(
        self, background_tasks: BackgroundTasks, dev_mode: bool = False
    ):
        agents = self.database_manager.query(
            Tables.AGENTS, ("id", "=", 1) if dev_mode else None
        )

        for agent in agents:
            proactive_rooms = self.database_manager.query(
                Tables.ROOMS,
                (Tables.ROOMS__agent_id, agent.id),
                (Tables.ROOMS__agent_proactivity, ">", 0),
            )

            for room in proactive_rooms:
                if self._is_room_eligible_for_revival(room, room.user_id):
                    last_message = self.database_manager.get_row(
                        Tables.MESSAGES,
                        {Tables.MESSAGES__room_id: room.id},
                        order_by=Tables.MESSAGES__created_at,
                        order_desc=True,
                    )

                    if last_message and self._should_send_proactive_message(
                        agent_proactivity=room.agent_proactivity,
                        last_message_time=last_message.created_at,
                    ):
                        revive_task = ReviveTask(room_id=room.id)
                        #TODO:
                        # 
                        # scheduled_task_info = ScheduledTaskInfo(
                        #     task=revive_task, delay=0
                        # )

                        # await SchedulerService.schedule_task(
                        #     task_data=scheduled_task_info.to_dict(),
                        #     delay=0,
                        #     db=self.database_manager,
                        # )

    def _is_room_eligible_for_revival(self, room: Room, user_id: str):
        if not room.subscribe_msg_sent:
            return True

        # TODO: add current date
        subscription = self.database_manager.get_row(
            Tables.SUBSCRIPTIONS,
            {
                Tables.SUBSCRIPTIONS__user_id: user_id,
                Tables.SUBSCRIPTIONS__status: SubscriptionStatus.ACTIVE
            },
        )

        return subscription is not None

    def _should_send_proactive_message(
        self,
        agent_proactivity: float,
        last_message_time: datetime,
        min_interval: timedelta = timedelta(minutes=30),
        max_interval: timedelta = timedelta(days=7),
    ) -> bool:
        """
        Determine if the agent should send a proactive message based on proactivity and time elapsed.

        Args:
        agent_proactivity - The agent's proactivity score (0 to 1).
        last_message_time - The timestamp of the last message in the room.
        min_interval - The minimum interval between messages.
        max_interval - The maximum interval between messages.

        Returns:
        bool: True if the agent should send a message, False otherwise.
        """
        current_time = datetime.now(timezone.utc)
        time_elapsed = current_time - last_message_time

        # Calculate how much of the total possible interval has elapsed
        interval_progress = (time_elapsed - min_interval) / (
            max_interval - min_interval
        )
        interval_progress = max(0, min(interval_progress, 1))  # Clamp between 0 and 1

        # Combine interval progress with agent proactivity
        send_probability = interval_progress * agent_proactivity

        return random.random() < send_probability
