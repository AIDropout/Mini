from mini.server.celery.celery import app
from mini.core.logger import get_logger
from config.container import container

logger = get_logger(__name__)


@app.task
def run_jobs():
    logger.info("This task runs every minute")

    # get all incomplete jobs that are due

    # add them to send message