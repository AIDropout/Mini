from config.config import config
from celery import Celery

celery_app = Celery("mini")

celery_app.conf.update(
    broker_url=config.REDIS_URL,
    result_backend=config.REDIS_URL,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

celery_app.autodiscover_tasks(
    ["mini.server.tasks.send_response", "mini.server.tasks.send_proactive"]
)
