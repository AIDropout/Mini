from celery import shared_task

from config.container import container
from mini.core.models.task.chat import ProactiveTask
from mini.core.logger import get_logger
from mini.core.models.message import MessagingProviderEnum
from mini.messaging.discord.discord import discord_manager


logger = get_logger(__name__)


@shared_task(bind=True, max_retries=2)
def send_proactive(self, provider_name: str, room_id: str):
    task = None
    provider_name = MessagingProviderEnum(provider_name)
    context_factory = container.get_context_factory()
    agent = container.get_agent_controller()

    try:
        context = context_factory.get_context_from_room_id(room_id)
        messaging_provider = context_factory.get_messaging_provider_from_context(
            context, provider_name
        )
        task = ProactiveTask(
            context=context,
            messaging_provider=messaging_provider,
        )
        result = agent.process_chat_task(task)

    except Exception as e:
        # TODO: handle task removal
        # if room_id and task.id:
        #     self.cancel_manager.remove_task(room_id, task.id)
        msg = discord_manager.log_error(f"room_id={room_id}")
        logger.exception(msg)
