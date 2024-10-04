from celery import chain, group, shared_task

from config.config import config
from config.container import container
from mini.core.enums import JobStatus, MessagingProviderType
from mini.core.logger import get_logger
from mini.server.celery.tasks.send_message import send_message
from mini.server.celery.celery import app

logger = get_logger(__name__)
job_table_service = container.job_table_service
session_table_service = container.session_table_service


@app.task
def run_cron():
    """
    Runs every x seconds. The interval is set in config in celeryconfig.py.
    
    1. End and process all stale sessions
    2. Run all due jobs
    3. Run all proactive messages
    """
    logger.info("Running cron...")

    # Process stale sessions
    session_table_service.process_stale_sessions()

    # Run all due jobs
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
