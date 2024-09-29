from datetime import timedelta
from config.config import config

broker_url = config.REDIS_URL
result_backend = config.REDIS_URL

task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
timezone = "UTC"
enable_utc = True
beat_schedule = {
    "run-every-x-seconds": {
        "task": "mini.server.celery.cron.run_jobs",
        "schedule": timedelta(seconds=config.PROACTIVE_CONFIG.cron_interval),
    },
}
