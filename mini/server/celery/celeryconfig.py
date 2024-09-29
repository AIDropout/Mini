from datetime import timedelta

from celery.schedules import crontab

from config.config import config

broker_url = config.REDIS_URL
result_backend = config.REDIS_URL

task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
timezone = "UTC"
enable_utc = True

beat_schedule = {
    "run-every-minute": {
        "task": "mini.server.celery.cron.run_jobs",
        # "schedule": crontab(), # Call every minute
        "schedule": timedelta(seconds=5),  # for debug
    },
}
