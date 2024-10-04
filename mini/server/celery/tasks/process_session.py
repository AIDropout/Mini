from celery import shared_task

from config.config import config
from mini.core.logger import get_logger
from mini.messaging.providers.discord import discord_manager

logger = get_logger(__name__)


@shared_task()
def process_session(
    session_id: str,
):
    """`"""
    from config.container import container

    try:
        messages = container.message_table_service.get_messages_in_session(session_id)

        # TODO: Run LLM to store user preferences into room

        # TODO: then, in agent, get and pass user preferences to Big LLm

    except Exception:
        msg = discord_manager.log_error(f"Error in processing session {session_id}")
        logger.exception(msg)
        raise
