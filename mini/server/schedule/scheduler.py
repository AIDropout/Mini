from datetime import datetime, timedelta

import requests
from pytz import timezone

from config.config import config
from mini.core.logger import get_logger
from mini.server.schedule.apscheduler import APScheduler
from mini.utils.time import TimeManager

logger = get_logger(__name__)


class Scheduler:
    def __init__(
        self, scheduler: APScheduler, system_time_manager: TimeManager
    ) -> None:
        self.engine = scheduler
        self.system_time_manager = system_time_manager

    @staticmethod
    def send_proactive_message(
        room_id: str, api_key: str, url: str = config.BACKEND_URL
    ):
        logger.info("Running proactive message for room %s", room_id)

        url = f"{url}/rooms/{room_id}/proactive"
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
        api_key = config.BACKEND_API_KEY
        job_id = self.engine.add_job(
            Scheduler.send_proactive_message,
            trigger="date",
            run_date=run_date,
            kwargs={"room_id": room_id, "api_key": api_key},
        )
        return job_id

    def schedule_proactive_message_from_now(
        self, room_id: str, minutes_from_now: float
    ) -> str:
        run_date = datetime.now(tz=timezone(self.engine.schedule_timezone)) + timedelta(
            minutes=minutes_from_now
        )
        job_id = self.schedule_proactive_message(room_id, run_date)
        return job_id

    def schedule_job(self, run_date, func, **kwargs) -> str:
        job_id = self.engine.add_job(func, trigger="date", run_date=run_date, **kwargs)
        return job_id

    def schedule_job_from_now(self, minutes_from_now, func, **kwargs) -> str:
        run_date = self.system_time_manager.get_user_datetime() + timedelta(
            minutes=minutes_from_now
        )
        job_id = self.engine.add_job(func, trigger="date", run_date=run_date, **kwargs)
        return job_id

    def remove_job(self, job_id: str) -> bool:
        return self.engine.remove_job(job_id)
