from datetime import datetime, timedelta
from typing import cast

import requests
from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from apscheduler.job import Job
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone

from config.config import config
from mini.core.logger import get_logger

logger = get_logger(__name__)


class TaskScheduler:
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

    def initialize(self) -> None:
        logger.info("🕰️ Starting scheduler")
        try:
            self.scheduler.start()
        except Exception as e:
            logger.error("Failed to start scheduler: %s", e)

    def close(self) -> None:
        logger.info("🛌 Closing scheduler")
        try:
            self.scheduler.shutdown(wait=False)
        except Exception as e:
            logger.error("Failed to close scheduler: %s", e)

    def _add_job(self, func, trigger, **kwargs) -> str:
        job = self.scheduler.add_job(func, trigger, **kwargs)
        logger.info(
            f"🕥 Scheduled Job added: {job.id} with trigger: {trigger} and kwargs {kwargs}"
        )
        return job.id

    @staticmethod
    def job_func(
        room_id: str,
        api_key: str,
        url: str = "https://32c7-132-161-243-149.ngrok-free.app",
    ):
        logger.info("Running proactive message for room %s", room_id)
        url = f"{url}/rooms/proactive/{room_id}"
        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.post(url, headers=headers, timeout=100)
            if response.status_code == 200:
                logger.info("Proactive message sent successfully: %s", response.json())
            else:
                logger.error(
                    "Failed to send proactive message, status code: %s",
                    response.status_code,
                )
        except Exception as e:
            logger.error("Error during proactive message API call: %s", e)

    def schedule_proactive_message(self, room_id: str, run_date: datetime) -> str:
        # should also cancel any existing proactive messages
        # also only build it as following:
        # new user: 4 hrs, 1 day user: 8 hrs, 5 days user: 48 hrs, else never
        api_key = config.BACKEND_API_KEY
        job_id = self._add_job(
            TaskScheduler.job_func,
            trigger="date",
            run_date=run_date,
            kwargs={"room_id": room_id, "api_key": api_key},
        )
        return job_id

    def schedule_proactive_message_from_now(
        self, room_id: str, minutes_from_now: float
    ) -> str:

        run_date = datetime.now(tz=timezone(self.schedule_timezone)) + timedelta(
            minutes=minutes_from_now
        )  # TODO: change to minutes
        job_id = self.schedule_proactive_message(room_id, run_date)
        return job_id

    def schedule_job(self, run_date, func, **kwargs) -> str:
        job_id = self._add_job(func, trigger="date", run_date=run_date, **kwargs)
        return job_id

    def schedule_job_from_now(self, minutes_from_now, func, **kwargs) -> str:
        run_date = datetime.now() + timedelta(minutes=minutes_from_now)
        job_id = self._add_job(func, trigger="date", run_date=run_date, **kwargs)
        return job_id

    def remove_job(self, job_id: str) -> bool:
        try:
            self.scheduler.remove_job(job_id)
            logger.info("Scheduled Job removed: %s", job_id)
            return True
        except Exception as e:
            logger.error("Failed to remove Scheduled Job %s: %s", job_id, e)
            return False

    def get_jobs(self):
        job_list = cast(list[Job], self.scheduler.get_jobs())
        logger.info("Current Scheduled Jobs: %s", job_list)
        return job_list

    def update_job(self, job_id: str, **kwargs) -> bool:
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
