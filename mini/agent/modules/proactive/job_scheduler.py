from datetime import datetime, timedelta
from typing import Optional

from mini.agent.modules.proactive.constants import (
    DEAD_ZONE_END,
    DEAD_ZONE_START,
    LONG_PROACTIVE_MESSAGE_DELAY,
    MEDIUM_PROACTIVE_MESSAGE_DELAY,
    RANDOM_HOUR_RANGE,
    SHORT_PROACTIVE_MESSAGE_DELAY,
)
from mini.agent.modules.proactive.models import ScheduledMessageTemplate
from mini.agent.modules.proactive.time_utils import (
    calculate_time_since,
    get_safe_datetime_in_future,
)
from mini.core.enums import JobStatus, MessageTaskType
from mini.database.tables.job_service import JobTableService
from mini.utils.time import TimeManager


class JobScheduler:
    def __init__(
        self, job_table_service: JobTableService, system_time_manager: TimeManager
    ):
        self.job_table_service = job_table_service
        self.system_time_manager = system_time_manager

    def get_next_scheduled_job_time_diff(self) -> Optional[timedelta]:
        """
        Get the time difference until the next scheduled job.

        Returns:
            Optional[timedelta]: The time difference between now and the next scheduled job
                                if one exists, None otherwise.
        """
        due_jobs = self.job_table_service.get_upcoming_jobs()

        if due_jobs and due_jobs[0]:
            scheduled_time = datetime.fromisoformat(due_jobs[0].scheduled_for)
            return -calculate_time_since(scheduled_time)
        return None

    def schedule_based_on_activity(
        self, time_diff: timedelta, room_id: str, log: str
    ) -> Optional[str]:
        """Determine when to schedule the next proactive message based on user activity."""
        if time_diff < SHORT_PROACTIVE_MESSAGE_DELAY:
            log += " A short delay proactive message scheduled."
            return self._schedule_message(
                room_id, log, time_delta_from_now=SHORT_PROACTIVE_MESSAGE_DELAY
            )
        elif time_diff < MEDIUM_PROACTIVE_MESSAGE_DELAY:
            log += " A medium delay proactive message scheduled."
            return self._schedule_message(
                room_id, log, time_delta_from_now=MEDIUM_PROACTIVE_MESSAGE_DELAY
            )
        elif time_diff < LONG_PROACTIVE_MESSAGE_DELAY:
            log += " A long delay proactive message scheduled."
            return self._schedule_message(
                room_id, log, time_delta_from_now=LONG_PROACTIVE_MESSAGE_DELAY
            )
        else:
            return None

    def schedule_based_on_messages(self) -> Optional[str]:
        """Schedule a message based on given data."""
        raise NotImplementedError()

    def schedule_based_on_current_events(self) -> Optional[str]:
        """Schedule a message based on memories."""
        raise NotImplementedError()

    def _schedule_message(
        self, room_id: str, log: str, time_delta_from_now: timedelta
    ) -> str:
        """Schedule a message for a future time, avoiding the dead zone."""
        safe_dispatch_time = get_safe_datetime_in_future(
            time_delta=time_delta_from_now,
            dead_start=DEAD_ZONE_START,
            dead_end=DEAD_ZONE_END,
            random_int=RANDOM_HOUR_RANGE,
        )

        # ScheduledMessageTemplate doesn't do anything for now
        scheduled_message = ScheduledMessageTemplate(
            reason_for_message="This chat hasn't been active in the past couple of hours",
            scheduled_time=safe_dispatch_time,
        )

        scheduled_timestamp = TimeManager.datetime_to_timestamp(
            scheduled_message.scheduled_time
        )
        self._save_scheduled_job(room_id, scheduled_timestamp, log)

        return scheduled_timestamp

    def _save_scheduled_job(self, room_id: str, scheduled_time: str, save_log: str):
        """Save a scheduled job to the database."""
        self.job_table_service.create_job(
            room_id=room_id,
            scheduled_for=scheduled_time,
            status=JobStatus.SCHEDULED,
            job_type=MessageTaskType.PROACTIVE,
            log=save_log,
        )
