from datetime import datetime, timedelta
from typing import Optional
import random
import pytz

from mini.core.logger import get_logger
from mini.core.models.context import Context
from mini.core.enums import JobStatus, MessageTaskType
from mini.database.tables.job_service import JobTableService
from mini.database.tables.room_service import RoomTableService
from mini.database.tables.message_service import MessageTableService
from mini.utils.time import TimeManager

logger = get_logger(__name__)


class ProactiveService:
    def __init__(
        self,
        system_time_manager: TimeManager,
        context: Context,
        job_table_service: JobTableService,
        room_table_service: RoomTableService,
        message_table_service: MessageTableService,
    ):
        self.context = context
        self.system_time_manager = system_time_manager
        self.job_table_service = job_table_service
        self.room_table_service = room_table_service
        self.message_table_service = message_table_service

    def schedule_proactive_message(self) -> Optional[str]:
        """
        1. Remove existing proactive jobs
        2. Calculate time till next send
            - Number of messages in room
            - Agent proactivity in room
            - Avoid night time
        3. Schedule next proactive job

        Returns:
            Optional[str]: The scheduled dispatch time as a string, or None if no message is scheduled.
        """

        self.job_table_service.remove_jobs_from_room(self.context.room.id)
        next_send_time = self._get_next_send_time()
        return self._schedule_proactive_job(next_send_time)

    def _get_next_send_time(self) -> str:
        """
        Determine the next send time for a proactive message.

        Factors considered:
        1. Number of messages in the room (random 12-36 hours delay for less active rooms)
        2. Agent proactivity
        3. Add 12-24 random hours if current time is between 7 PM and 7 AM EST

        Returns:
            str: The next send time for the proactive message as a timestamp string
        """
        message_count = self.message_table_service.get_room_message_count(
            self.context.room.id
        )
        agent_proactivity = self.context.room.agent_proactivity

        # Base delay calculation
        if message_count < 10:
            # Random delay between 12 and 36 hours for less active rooms
            base_delay = timedelta(hours=random.uniform(12, 36))
        else:
            base_delay = timedelta(hours=12)  # Shorter delay for more active rooms

        # Adjust delay based on agent proactivity (assuming 0-1 scale)
        adjusted_delay = base_delay * (2 - agent_proactivity)

        # Calculate initial send time
        current_time = self.system_time_manager.get_user_datetime()
        next_send_time = current_time + adjusted_delay

        # Convert the time to EST
        est = pytz.timezone("US/Pacific")
        est_time = next_send_time.astimezone(est)

        # Check if the time is between 7 PM and 7 AM EST
        if est_time.hour >= 19 or est_time.hour < 7:
            # Add a random delay between 12 and 24 hours
            additional_delay = timedelta(hours=random.uniform(12, 24))
            next_send_time += additional_delay

        return self.system_time_manager.datetime_to_timestamp(next_send_time)

    def _schedule_proactive_job(
        self,
        timestamp: datetime,
        log: str,
    ) -> str:
        """Schedule a message for a future time, avoiding the dead zone."""
        converted_timestamp = TimeManager.datetime_to_timestamp(timestamp)
        return self.job_table_service.create_job(
            room_id=self.context.room.id,
            scheduled_for=converted_timestamp,
            status=JobStatus.SCHEDULED,
            job_type=MessageTaskType.PROACTIVE,
            log=log,
        )
