from config.container import container
from mini.core.logger import get_logger
from mini.core.models.message import MessagingProviderType
from mini.messaging.send_message.send_message import send_message
from mini.server.celery.celery import app

logger = get_logger(__name__)


@app.task
def run_jobs():
    logger.info("---Cron---")
    job_service = container.job_table_service
    jobs = job_service.get_due_jobs()

    for job in jobs:
        logger.info(f"🤩 running job {job.id}")
        send_message.delay(
            provider_name=MessagingProviderType.BIRD.value,
            room_id=job.room_id,
            type=job.type,
            job_id=job.id,
        )
