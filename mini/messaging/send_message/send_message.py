from celery import shared_task
from celery.exceptions import Ignore as Canceled

from config.config import config
from config.container import container
from mini.core.logger import get_logger
from mini.core.models.message import MessagingProviderType
from mini.messaging.providers.discord import discord_manager
from mini.core.enums import MessageTaskType
from mini.agent.build_agent import build_agent
from mini.messaging.send_message.cancellable import CancellableTask

logger = get_logger(__name__)

messaging_service = container.messaging_service
paywall_service = container.paywall_service
CancellableTask.init_redis(container.redis_manager)


@shared_task(bind=True, base=CancellableTask)
def send_message(self: CancellableTask, provider_name: str, room_id: str, type: str):
    self.register_task(room_id)

    try:
        task = messaging_service.build_message_task(
            MessagingProviderType(provider_name), room_id, MessageTaskType(type)
        )

        if type == MessageTaskType.RESPONSE.value:
            paywall_service.handle_subscription_check(task)

        self.check_cancellation()

        agent = build_agent(config, task.context)

        return agent.process_message_task(task, self.check_cancellation)
    except Canceled:
        pass
    except Exception:
        msg = discord_manager.log_error(f"room_id={room_id}")
        logger.exception(msg)
