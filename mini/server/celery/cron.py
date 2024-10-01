from celery import shared_task, chain, group
from celery.exceptions import Ignore as Canceled

from config.config import config
from config.container import container
from mini.core.enums import JobStatus
from mini.core.logger import get_logger
from mini.core.enums import MessagingProviderType
from mini.messaging.send_message.send_message import send_message
from mini.server.celery.celery import app

logger = get_logger(__name__)
job_table_service = container.job_table_service


@app.task
def run_jobs():
    # logger.info("Running cron...")

    jobs = job_table_service.get_due_jobs(is_local=config.is_local())

    job_chains = [
        # Chain celery tasks one after another
        chain(
            update_job_status.si(job.id, JobStatus.IN_PROGRESS.value),
            send_message.si(MessagingProviderType.BIRD.value, job.room_id, job.type),
            update_job_status.si(job.id, JobStatus.COMPLETE.value),
        ).on_error(handle_chain_error.s(job.id))
        for job in jobs
    ]

    # Execute all chain concurrently
    group(job_chains).apply_async()

@shared_task
def update_job_status(job_id: str, status: str):
    logger.info(f"Updating job id {job_id} to status: {status}")
    job_table_service.update_job_status(job_id, JobStatus(status))


@shared_task
def handle_chain_error(request, exc, traceback, job_id):
    logger.error(f"Chain failed for job {job_id}: {str(exc)}")
    job_table_service.update_job_status(job_id, JobStatus.ERROR)
    job_table_service.update_job_log(job_id, f"Job failed: {str(exc)}\n{traceback}")
