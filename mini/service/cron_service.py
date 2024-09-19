# services/room_service.py
import random
from datetime import datetime, timedelta, timezone

from config.config import config
from mini.controller.task import ReviveTask
from mini.core.logger import get_logger
from mini.core.schema.subscription import SubscriptionStatus
from mini.core.schema.tables import Message, Room, Tables, User
from mini.storage.database import DatabaseManager
from mini.manager.messaging import MessagingManager
from mini.service.base import Service

logger = get_logger(__name__)


class CronService(Service):
    def __init__(
        self, database_manager: DatabaseManager, messaging_manager: MessagingManager
    ):
        super().__init__(database_manager)
        self.messaging_manager = messaging_manager

    def refresh_rooms(self, dev_mode: bool = False):
        agents = self.database_manager.get_multiple_rows(
            table_name=Tables.AGENTS,
            max_rows=100,
            order_by="id",
            order_desc=False,
            conditions=(
                {Tables.AGENTS__bird_channel_id: config.BIRD_DEV_CHANNEL_ID}
                if dev_mode
                else None
            ),
        )

        for agent in agents:

            proactive_rooms = self.database_manager.query(
                Tables.ROOMS,
                (Tables.ROOMS__agent_id, agent.id),
                (Tables.ROOMS__agent_proactivity, ">", 0),
            )

            # logger.info(proactive_rooms)

        #     for room in proactive_rooms:
        #         if self._is_room_eligible_for_revival(room, room.user_id):
        #             last_message = self.database_manager.get_row(
        #                 Tables.MESSAGES,
        #                 {Tables.MESSAGES__room_id: room.id},
        #                 order_by=Tables.MESSAGES__created_at,
        #                 order_desc=True,
        #             )

        #             if last_message and self._should_send_proactive_message(
        #                 agent_proactivity=room.agent_proactivity,
        #                 last_message_time=last_message.created_at,
        #             ):
        #                 revive_task = ReviveTask(room_id=room.id)
        # TODO:
        #
        # scheduled_task_info = ScheduledTaskInfo(
        #     task=revive_task, delay=0
        # )

        # await SchedulerService.schedule_task(
        #     task_data=scheduled_task_info.to_dict(),
        #     delay=0,
        #     db=self.database_manager,
        # )

    def _is_room_eligible_for_revival(self, room: Room, user_id: str) -> bool:
        if room.subscribe_msg_sent:
            return False

        subscription = self.database_manager.get_row(
            Tables.SUBSCRIPTIONS,
            {
                Tables.SUBSCRIPTIONS__user_id: user_id,
                Tables.SUBSCRIPTIONS__status: SubscriptionStatus.ACTIVE,
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
