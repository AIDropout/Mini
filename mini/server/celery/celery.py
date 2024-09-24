from celery import Celery
from fastapi import HTTPException

from config.config import config

from mini.core.logger import get_logger

app = Celery("mini")

app.config_from_object("mini.server.celery.celeryconfig")

app.autodiscover_tasks(
    ["mini.messaging.tasks.tasks"]
)