from typing import List, Optional

from mini.core.logger import get_logger
from mini.database.models import Tables, Job
from mini.core.enums import JobStatus
from mini.database.database import DatabaseManager
from mini.utils.time import TimeManager


logger = get_logger(__name__)


class JobTableService:
    def __init__(self, database_manager: DatabaseManager, time_manager: TimeManager):
        self.database_manager = database_manager
        self.time_manager = time_manager

    def create_job(
        self,
        room_id: str,
        run_at: str,
        job_type: str,
    ) -> None:

        job = Job(room_id=room_id, run_at=run_at, type=job_type)

        self.database_manager.insert(Tables.JOBS, job)

    def get_due_jobs(self) -> Optional[List[Job]]:
        """
        Get scheduled jobs that are due
        """
        current_time = self.time_manager.get_user_datetime()

        jobs = self.database_manager.query(
            Tables.JOBS,
            (Tables.JOBS__status, JobStatus.SCHEDULED.value),
            (Tables.JOBS__scheduled_for, "<=", current_time.isoformat()),
        )

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
