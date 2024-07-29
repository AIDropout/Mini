from celery import Celery
from config.config import config

celery_app = Celery(
    'zootopia',
    broker=config.REDIS_URL,
    backend=config.REDIS_URL,
    include=['zootopia.server.tasks']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)