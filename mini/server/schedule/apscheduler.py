from typing import cast

from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from apscheduler.job import Job
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone

from mini.core.logger import get_logger

logger = get_logger(__name__)


class APScheduler:
    def __init__(self, db_url: str, schedule_timezone: str = "US/Central") -> None:
        self.db_url = db_url
        jobstores = {"default": SQLAlchemyJobStore(url=self.db_url)}
        executors = {
            "default": ThreadPoolExecutor(20),
            "processpool": ProcessPoolExecutor(5),
        }
        job_defaults = {"coalesce": False, "max_instances": 1}
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=timezone(schedule_timezone),
        )
        self.schedule_timezone = schedule_timezone

        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            logger.info("Reattempted initialization: APScheduler already initialized!")
            return
        logger.info("🕰️ Starting scheduler")
        try:
            self.scheduler.start()
            self._initialized = True
        except Exception as e:
            logger.error("Failed to start scheduler: %s", e)

    def close(self) -> None:
        logger.info("🛌 Closing scheduler")
        try:
            self.scheduler.shutdown(wait=False)
            self._initialized = False
        except Exception as e:
            logger.error("Failed to close scheduler: %s", e)

    def add_job(self, func, trigger, **kwargs) -> str:
        if not self._initialized:
            self.initialize()
        job = self.scheduler.add_job(func, trigger, **kwargs)
        logger.info(
            "🕥 Scheduled Job added: %s with trigger: %s and kwargs %s",
            job.id,
            trigger,
            kwargs,
        )
        return job.id

    def remove_job(self, job_id: str) -> bool:
        if not self._initialized:
            self.initialize()
        try:
            self.scheduler.remove_job(job_id)
            logger.info("Scheduled Job removed: %s", job_id)
            return True
        except Exception as e:
            logger.error("Failed to remove Scheduled Job %s: %s", job_id, e)
            return False

    def get_jobs(self):
        if not self._initialized:
            self.initialize()
        job_list = cast(list[Job], self.scheduler.get_jobs())
        logger.info("Current Scheduled Jobs: %s", job_list)
        return job_list

    def update_job(self, job_id: str, **kwargs) -> bool:
        if not self._initialized:
            self.initialize()
        try:
            job = cast(Job, self.scheduler.get_job(job_id))
            if job:
                job.modify(**kwargs)
                logger.info("Scheduled Job updated: %s", job_id)
                return True
            else:
                logger.warning("Scheduled Job not found: %s", job_id)
                return False
        except Exception as e:
            logger.error("Failed to update Scheduled Job %s: %s", job_id, e)
            return False
