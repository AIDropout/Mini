from celery import shared_task

from config.container import container
from mini.core.logger import get_logger
from mini.core.models.message import MessagingProviderEnum
from mini.messaging.providers.discord import discord_manager

logger = get_logger(__name__)

chat_task_factory = container.get_chat_task_factory()
admin_service = container.get_messaging_admin_service()
agent = container.get_agent_controller()


@shared_task
def send_proactive(provider_name: str, room_id: str):
    try:
        task = chat_task_factory.build_proactive_task(
            MessagingProviderEnum(provider_name), room_id
        )
        return agent.process_chat_task(task)
    except Exception as e:
        msg = discord_manager.log_error(f"room_id={room_id}")
        logger.exception(msg)


@shared_task
def send_response(provider_name: str, request_body: dict):
    try:
        task = chat_task_factory.build_response_task(
            MessagingProviderEnum(provider_name), request_body
        )

        admin_service.process_response_task(task)

        agent.process_chat_task(task)

    except Exception as e:
        msg = discord_manager.log_error(f"error")
        logger.exception(msg)





