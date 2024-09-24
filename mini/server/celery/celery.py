from celery import Celery
from fastapi import HTTPException

from config.config import config

from mini.core.logger import get_logger

app = Celery("mini")

app.config_from_object("mini.server.celery.celeryconfig")

app.autodiscover_tasks(
    ["mini.server.tasks.send_response", "mini.server.tasks.send_proactive"]
)


def check_celery_worker():
    try:
        # Ping the worker to check if it's alive
        result = celery_app.control.ping(timeout=1)
        if not result:
            raise Exception("No running Celery workers were found.")
    except (TimeoutError, Exception) as e:
        raise HTTPException(
            status_code=503, detail=f"Celery is not available: {str(e)}"
        )
