from typing import List, Optional

from fastapi import HTTPException

from mini.core.logger import get_logger
from mini.database.models import Tables, Job
from mini.core.models.jobs import JobStatus
from mini.database.database import DatabaseManager

logger = get_logger(__name__)


class JobTableService:
    def __init__(
        self,
        database_manager: DatabaseManager,
    ):
        self.database_manager = database_manager

    def create_job(
        self,
        room_id: str,
        run_at: str,
        job_type: str,
    ) -> None:

        job = Job(room_id=room_id, run_at=run_at, type=job_type)

        self.database_manager.insert(Tables.JOBS, job)

    def get_most_recent_job(self, room_id: str):
        pass

    def update_job_status(self, job_id: str, status: JobStatus) -> None:
        updated_job = self.database_manager.update(
            table_name=Tables.JOBS,
            update_data={
                Tables.JOBS__status: status,
            },
            condition_key=Tables.JOBS__id,
            condition_value=job_id,
        )

    def update_job_log(self, job_id: str, log: str) -> None:
        updated_job = self.database_manager.update(
            table_name=Tables.JOBS,
            update_data={
                Tables.JOBS__log: log,
            },
            condition_key=Tables.JOBS__id,
            condition_value=job_id,
        )

    def remove_job(self, job_id: str) -> None:
        pass
