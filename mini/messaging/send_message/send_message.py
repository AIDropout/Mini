from celery import shared_task
from celery.exceptions import Ignore as Canceled
from typing import Optional

from config.config import config
from config.container import container
from mini.core.logger import get_logger
from mini.core.models.message import MessagingProviderType
from mini.core.enums import JobStatus
from mini.messaging.providers.discord import discord_manager
from mini.core.enums import MessageTaskType
from mini.agent.build_agent import build_agent
from mini.messaging.send_message.cancellable import CancellableTask

logger = get_logger(__name__)

messaging_service = container.messaging_service
paywall_service = container.paywall_service
job_table_service = container.job_table_service
CancellableTask.init_redis(container.redis_manager)


@shared_task(bind=True, base=CancellableTask)
def send_message(
    self: CancellableTask,
    provider_name: str,
    room_id: str,
    type: str,
    job_id: Optional[str] = None,
):
    self.register_task(room_id)

    def update_job_status(status: JobStatus):
        logger.info(f"updating job id 🔴 {job_id} to 🔴 {status.value}")
        if job_id:
            job_table_service.update_job_status(job_id, status)

    update_job_status(JobStatus.IN_PROGRESS)

    try:
        task = messaging_service.build_message_task(
            MessagingProviderType(provider_name), room_id, MessageTaskType(type)
        )

        if type == MessageTaskType.RESPONSE.value:
            paywall_service.handle_subscription_check(task)

        self.check_cancellation()

        agent = build_agent(config, task.context)

        success = agent.process_message_task(task, self.check_cancellation)

        update_job_status(JobStatus.COMPLETE)

    except Canceled:
        pass
    except Exception:
        msg = discord_manager.log_error(f"room_id={room_id}")
        update_job_status(JobStatus.ERROR)
        job_table_service.update_job_log(job_id, msg)
        logger.exception(msg)
