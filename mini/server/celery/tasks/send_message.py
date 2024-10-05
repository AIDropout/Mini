from celery import shared_task
from celery.exceptions import Ignore as Canceled

from config.config import config
from config.container import container
from mini.core.logger import get_logger
from mini.core.enums import MessagingProviderType
from mini.messaging.providers.discord import discord_manager
from mini.core.enums import MessageTaskType
from mini.agent.build_agent import build_agent
from mini.server.redis.cancellable import CancellableTask

logger = get_logger(__name__)

messaging_service = container.message_task_factory
paywall_service = container.paywall_service
CancellableTask.init_redis(container.redis_manager)

@shared_task(bind=True, base=CancellableTask)
def send_message(
    self: CancellableTask,
    provider_name: str,
    room_id: str,
    type: str,
):
    try:
        self.room_id = room_id

        logger.info(f"🩷🩷 checking task {self.request.id}")

        self.check_cancellation()

        task = messaging_service.build_message_task(
            MessagingProviderType(provider_name), room_id, MessageTaskType(type)
        )

        if type == MessageTaskType.RESPONSE.value:
            paywall_service.handle_subscription_check(task)

        self.check_cancellation()

        agent = build_agent(config, task.context)

        agent.process_message_task(task, self.check_cancellation)

    except Canceled:
        logger.info(f"Task cancelled for room_id={room_id}")
        raise
    except Exception:
        msg = discord_manager.log_error(f"room_id={room_id}")
        logger.exception(msg)
        raise
