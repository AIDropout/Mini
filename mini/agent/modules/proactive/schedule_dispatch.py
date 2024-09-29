from typing import Optional

from mini.agent.modules.base import AgentModule
from mini.agent.modules.proactive.job_scheduler import JobScheduler
from mini.agent.modules.proactive.time_utils import (
    calculate_time_since,
    format_time_diff,
)
from mini.core.logger import get_logger
from mini.core.models.context import Context
from mini.database.database import DatabaseManager
from mini.database.tables.job_service import JobTableService
from mini.utils.time import TimeManager

logger = get_logger(__name__)


class ScheduleDispatch(AgentModule):
    def __init__(
        self,
        database_manager: DatabaseManager,
        job_table_service: JobTableService,
        system_time_manager: TimeManager,
        context: Context,
    ):
        super().__init__(database_manager, context)
        self.job_scheduler = JobScheduler(job_table_service, system_time_manager)
        self.context = context

    def schedule_proactive_message(self) -> Optional[str]:
        """
        Schedule a proactive message based on user activity and retention strategies.

        Returns:
            Optional[str]: The scheduled dispatch time as a string, or None if no message is scheduled.
        """
        already_scheduled_time_diff = (
            self.job_scheduler.get_next_scheduled_job_time_diff()
        )
        if already_scheduled_time_diff:
            logger.info(
                "⏳ Proactive message already scheduled (not scheduling). "
                "Will send message in %s hours.",
                already_scheduled_time_diff.total_seconds() // 3600,
            )
            return None

        time_diff = calculate_time_since(self.context.room.last_msg_sent_at)
        log = f"User was active {format_time_diff(time_diff)} ago."

        # notice future job_scheduler can also schedule based on messages, data, etc.
        scheduled_timestamp = self.job_scheduler.schedule_based_on_activity(
            time_diff, self.context.room.id, log
        )

        if scheduled_timestamp:
            logger.info(
                "⏳ Scheduling proactive message (scheduled at: %s): %s",
                scheduled_timestamp,
                log,
            )
        else:
            logger.info(
                "Inactive user detected. Not scheduling proactive message. "
                "User has not been active for %s hours (%s days)",
                time_diff.total_seconds() // 3600,
                time_diff.days,
            )

        return scheduled_timestamp
