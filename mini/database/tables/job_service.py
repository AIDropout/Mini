from typing import List, Optional, cast

from mini.core.enums import JobStatus, MessageTaskType
from mini.core.logger import get_logger
from mini.database.database import DatabaseManager
from mini.database.models import Job, Tables
from mini.utils.time import TimeManager

logger = get_logger(__name__)


class JobTableService:
    def __init__(
        self, database_manager: DatabaseManager, system_time_manager: TimeManager
    ):
        self.database_manager = database_manager
        self.system_time_manager = system_time_manager

    def create_job(
        self,
        room_id: str,
        job_type: MessageTaskType,
        scheduled_for: str,
        status: JobStatus,
        log: str = "no log set when creating job",
    ):

        job = Job(
            room_id=room_id,
            type=job_type.value,
            scheduled_for=scheduled_for,
            status=status.value,
            log=log,
        )

        return self.database_manager.insert(Tables.JOBS, job)

    def get_due_jobs(self) -> Optional[List[Job]]:
        """
        Get scheduled jobs that are due
        """
        current_time = self.system_time_manager.get_user_datetime()

        jobs = self.database_manager.query(
            Tables.JOBS,
            (Tables.JOBS__status, JobStatus.SCHEDULED.value),
            (Tables.JOBS__scheduled_for, "<=", current_time.isoformat()),
        )

        jobs = cast(List[Job], jobs)
        return sorted(jobs, key=lambda job: job.scheduled_for)

    def get_upcoming_jobs(self) -> Optional[List[Job]]:
        """
        Get scheduled jobs that are upcoming
        """
        current_time = self.system_time_manager.get_user_datetime()

        jobs = self.database_manager.query(
            Tables.JOBS,
            (Tables.JOBS__status, JobStatus.SCHEDULED.value),
            (Tables.JOBS__scheduled_for, ">=", current_time.isoformat()),
        )

        jobs = cast(List[Job], jobs)
        return sorted(jobs, key=lambda job: job.scheduled_for)

    def get_most_recent_job(self, room_id: str) -> Job:
        pass

    def update_job_status(self, job_id: str, status: JobStatus) -> None:

        updated_job = self.database_manager.update(
            table_name=Tables.JOBS,
            update_data={
                Tables.JOBS__status: status.value,
            },
            condition_key=Tables.JOBS__id,
            condition_value=job_id,
        )
        logger.info(f"RESULT 🔴🔴🔴")
        logger.info(updated_job)

    def update_job_log(self, job_id: str, log: str) -> None:
        updated_job = self.database_manager.update(
            table_name=Tables.JOBS,
            update_data={
                Tables.JOBS__log: log,
            },
            condition_key=Tables.JOBS__id,
            condition_value=job_id,
        )

    def remove_jobs_from_room(self, room_id: str) -> None:
        """
        Would be used if a user deletes account or doesn't want to be texted anymore.
        """
        pass


if __name__ == "__main__":
    from config.container import container

    service = container.job_table_service
    jobs = service.get_due_jobs()
    logger.info(jobs)
