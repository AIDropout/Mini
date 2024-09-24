from celery import shared_task

from config.config import config
from config.container import container
from mini.core.logger import get_logger
from mini.core.models.message import MessagingProviderEnum, MiniMessage
from mini.messaging.providers.discord import discord_manager
from mini.database.database import DatabaseManager
from mini.database.models import Tables, Message
from mini.core.models.context import Context
from mini.messaging.providers import MessagingProvider

logger = get_logger(__name__)

chat_task_factory = container.get_chat_task_factory()
database_manager = container.database_manager
agent = container.get_agent_controller()


@shared_task
def send_proactive(provider_name: str, room_id: str):
    try:
        task = chat_task_factory.build_proactive_task(
            MessagingProviderEnum(provider_name), room_id
        )
        return agent.process_chat_task(task)
    except Exception as e:
        # TODO: remove task
        msg = discord_manager.log_error(f"room_id={room_id}")
        logger.exception(msg)


@shared_task
def send_response(provider_name: str, request_body: dict):
    try:
        task = chat_task_factory.build_response_task(
            MessagingProviderEnum(provider_name), request_body
        )

        handle_return_cases(
            task.message, task.context, database_manager, task.messaging_provider
        )
        insert_and_log_user_message(task.message, task.context, database_manager)

        agent.process_chat_task(task)

    except Exception as e:
        # TODO: remove task
        msg = discord_manager.log_error(f"error")
        logger.exception(msg)


# TODO: Put these funcs, along with subscribe logic into an admin manager
def handle_return_cases(
    message: MiniMessage,
    context: Context,
    database_manager: DatabaseManager,
    messaging_provider: MessagingProvider,
):
    if context.room.disabled_by_admin:
        logger.warning(f"Room {context.room.id} disabled. Canceling process.")
        raise ValueError("Room disabled by admin")

    if message.content == config.SECRET_PHRASES.reset_user:
        database_manager.supabase.auth.admin.delete_user(context.user.id)
        database_manager.delete(Tables.USERS, {Tables.USERS__id: context.user.id})
        messaging_provider.send_message(
            text="Successfully deleted your user from Auth tables and Users table"
        )
        return

    if context.room.disabled_by_admin:
        logger.warning(f"Room {context.room.id} disabled. Canceling process.")
        return False


def insert_and_log_user_message(
    message: MiniMessage, context: Context, database_manager: DatabaseManager
):
    database_manager.insert(
        Tables.MESSAGES,
        Message(
            room_id=context.room.id,
            sender_id=context.user.id,
            content=message.content,
        ),
    )

    if config.ENVIRONMENT == "production":
        discord_manager.log_message(
            message=f"-# {context.user.phone_number} -> {context.agent.name}: {message.content}"
        )
