from mini.server.celery.celery import app
from mini.core.logger import get_logger
from config.container import container

logger = get_logger(__name__)


@app.task
def send_proactive_messages():
    logger.info("This task runs every minute")
    cron_service = container.get_cron_service()
    cron_service.refresh_rooms()
