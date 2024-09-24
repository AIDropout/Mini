from config.config import config
from celery import Celery

from mini.core.logger import get_logger

app = Celery("mini")

app.config_from_object("mini.server.celery.celeryconfig")

app.autodiscover_tasks(
    ["mini.server.tasks.send_response", "mini.server.tasks.send_proactive"]
)
