from mini.server.celery.celery import app
from mini.utils.utils import logger

@app.task
def send_proactive_messages():
    logger.info("This task runs every minute")