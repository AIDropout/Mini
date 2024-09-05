from config.config import config
from celery.schedules import crontab

broker_url = config.REDIS_URL
result_backend = config.REDIS_URL

task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
timezone = "UTC"
enable_utc = True
# worker_pool = "solo"

from datetime import timedelta

beat_schedule = {
    'run-every-minute': {
        'task': 'mini.server.celery.cron.send_proactive_messages',
        # 'schedule': crontab(),
        'schedule': timedelta(seconds=10),

    },
}
