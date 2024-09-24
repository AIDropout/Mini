from celery import shared_task

from config.config import config
from config.container import container
from mini.core.logger import get_logger
from mini.core.models.message import MessagingProviderEnum
from mini.messaging.providers.discord import discord_manager
from mini.agent.agent_builder import build_agent

logger = get_logger(__name__)

chat_task_factory = container.get_chat_task_factory()
admin_service = container.get_messaging_admin_service()


@shared_task
def send_proactive(provider_name: str, room_id: str):
    try:
        task = chat_task_factory.build_proactive_task(
            MessagingProviderEnum(provider_name), room_id
        )
        agent = build_agent(config, task.context)
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
        processed_task = admin_service.process_response_task(task)
        
        agent = build_agent(config, task.context)
        return agent.process_chat_task(processed_task)
    except Exception as e:
        msg = discord_manager.log_error(f"error")
        logger.exception(msg)
