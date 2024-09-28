import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from mini.agent.modules.base import AgentModule
from mini.agent.modules.proactive.models import ScheduledMessageTemplate
from mini.core.logger import get_logger
from mini.core.models.context import Context
from mini.database.database import DatabaseManager
from mini.database.models import Tables
from mini.server.schedule.scheduler import Scheduler
from mini.utils.time import TimeManager

logger = get_logger(__name__)


class ScheduleDispatch(AgentModule):
    def __init__(
        self,
        database_manager: DatabaseManager,
        context: Context,
        scheduler: Scheduler,
    ):
        """
        Initialize the ScheduleDispatch class with dead zone timings and the random hour range.
        """
        super().__init__(database_manager, context)
        self.scheduler = scheduler

    def _remove_currently_scheduled_job(self) -> bool:
        previous_schedule_id = self.context.room.scheduled_send_id
        if previous_schedule_id is not None:
            self.scheduler.remove_job(job_id=previous_schedule_id)
            return True
        return False

    def _save_scheduled_job(self, scheduled_send_id: str):
        self.database_manager.update(
            Tables.ROOMS.value,
            update_data={Tables.ROOMS__scheduled_send_id: scheduled_send_id},
            condition_key=Tables.ROOMS__id,
            condition_value=self.context.room.id,
        )

    def _schedule_from_current_events(self) -> ScheduledMessageTemplate:
        raise NotImplementedError("idea is to schedule proactive from current events")

    def _schedule_from_message_content(
        self, message_content: str
    ) -> ScheduledMessageTemplate:
        raise NotImplementedError("idea is to schedule proactive from given message")

    def _schedule_from_time(
        self,
        hours_from_now: int,
        dead_start: int = 23,
        dead_end: int = 8,
        random_int: int = 3,
    ) -> ScheduledMessageTemplate:
        safe_dispatch_time = self.get_safe_datetime_in_future(
            hours_from_now=hours_from_now,
            dead_start=dead_start,
            dead_end=dead_end,
            random_int=random_int,
        )
        logger.info("Proactive message is scheduled to send at: %s", safe_dispatch_time)

        return ScheduledMessageTemplate(
            reason_for_message="This chat hasn't been active in the past couple of hours",
            scheduled_time=safe_dispatch_time,
        )

    @staticmethod
    def get_safe_datetime_in_future(
        hours_from_now: int,
        dead_start: int,
        dead_end: int,
        random_int: int,
        timezone: str = "UTC",
    ):
        """
        Calculate a datetime a given number of hours from now, but if it's within the dead zone,
        return a random time between dead_end and dead_end + random_int hours, with a random minute.

        Args:
        - hours_from_now: Number of hours from the current time to calculate.
        - dead_start: Start of the dead zone (hour in 24-hour format).
        - dead_end: End of the dead zone (hour in 24-hour format).
        - random_int: Max additional hours after dead_end for randomization.
        - timezone: Timezone string, defaults to UTC.

        Returns:
        - A datetime object either `hours_from_now` or adjusted based on the dead zone.
        """
        current_time = TimeManager(user_timezone=timezone).get_user_datetime()
        future_time = current_time + timedelta(hours=hours_from_now)

        # Extract hour and minute from the resulting time
        future_hour = future_time.hour

        # If the hour is within the dead zone, calculate a random time after the dead_end
        if dead_start <= future_hour or future_hour < dead_end:
            random_extra_hours = random.randint(0, random_int)
            random_extra_minutes = random.randint(0, 59)  # Random minute from 0 to 59
            random_extra_seconds = random.randint(0, 59)  # Random second from 0 to 59
            # Adjust time to be after dead_end with randomization
            adjusted_time = future_time.replace(
                hour=dead_end, minute=0, second=0, microsecond=0
            ) + timedelta(
                hours=random_extra_hours,
                minutes=random_extra_minutes,
                seconds=random_extra_seconds,
            )
            return adjusted_time

        return future_time

    def schedule_proactive_message(self):
        """
        Schedule a proactive message based on user activity and retention strategies.

        The function uses the last message time to decide when to send a proactive message:
        - If the user has been active recently (within 1 day), schedule a message soon.
        - For moderate inactivity (1 to 3 days), schedule a follow-up.
        - For extended inactivity (3 to 7 days), schedule a re-engagement message.
        - If the user has been inactive for more than 7 days, do not send a proactive message.
        """

        # 1. Remove any previously scheduled proactive message to avoid conflicts
        is_removed = self._remove_currently_scheduled_job()
        if is_removed:
            logger.info("Removed previously scheduled proactive message")

        # Get the current time as an offset-aware datetime
        now = datetime.now(ZoneInfo("UTC"))  # Set your desired timezone
        last_msg_time = self.context.room.last_msg_sent_at

        # Ensure last_msg_time is offset-aware. If it's not, convert it accordingly.
        if last_msg_time.tzinfo is None:
            logger.warning(
                "last_msg_time is naive, converting to offset-aware using America/Chicago"
            )
            last_msg_time = last_msg_time.replace(tzinfo=ZoneInfo("America/Chicago"))

        # Calculate the time difference
        time_diff = now - last_msg_time
        days_diff = time_diff.days

        # 2. Determine when to send the proactive message based on user activity

        # Less than 1 day since the last message: Low risk of disengagement
        # Send a soft reminder in 6 hours to maintain engagement
        if time_diff < timedelta(days=1):
            scheduled_message_template = self._schedule_from_time(hours_from_now=7)
            logger.info(
                "User was recently active, scheduling a soft reminder in 6 hours."
            )

        # Between 1 and 3 days: Moderate risk of disengagement
        # Send a follow-up message in 24-48 hours to keep the user engaged
        elif time_diff < timedelta(days=3):
            scheduled_message_template = self._schedule_from_time(hours_from_now=48)
            logger.info(
                "User moderately inactive, scheduling a follow-up message in 48 hours."
            )

        # Between 3 and 7 days: High risk of disengagement
        # Send a more proactive message in 72 hours (3 days) to re-engage the user
        elif time_diff < timedelta(days=7):
            scheduled_message_template = self._schedule_from_time(hours_from_now=72)
            logger.info(
                "User highly inactive, scheduling a proactive re-engagement in 72 hours."
            )

        # More than 7 days: Consider the user inactive
        # Do not schedule a proactive message to avoid overwhelming the user
        else:
            logger.info(
                "Inactive user detected. Not scheduling proactive message. "
                "User has not been active for %s hours (%s days)",
                time_diff.total_seconds() // 3600,
                days_diff,
            )
            return None

        # 3. Schedule the proactive message for the determined time
        next_dispatch_time = scheduled_message_template.scheduled_time
        schedule_id = self.scheduler.schedule_proactive_message(
            room_id=self.context.room.id, run_date=next_dispatch_time
        )
        self._save_scheduled_job(scheduled_send_id=schedule_id)

        logger.info("Proactive message is scheduled to send at: %s", next_dispatch_time)
        return next_dispatch_time
