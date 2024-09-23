from celery import shared_task
from datetime import datetime, timedelta

from config.config import config
from config.container import container
from mini.core.models.task.chat import ResponseTask
from mini.database.database import DatabaseManager
from mini.database.models import Tables, Message
from mini.core.logger import get_logger
from mini.core.models.context import Context
from mini.core.models.message import MessagingProviderEnum, MiniMessage
from mini.messaging.discord.discord import discord_manager
from mini.messaging import messaging_providers, MessagingProvider


logger = get_logger(__name__)


# TODO: Use a Bird request body
@shared_task(bind=True, max_retries=2)
def send_response(self, provider_name: str, request_body: dict):
    provider_name = MessagingProviderEnum(provider_name)
    context_factory = container.get_context_factory()
    database_manager = container.database_manager
    cancel_manager = container.get_cancel_manager()
    agent = container.get_agent_controller()
    task = None

    try:
        # Get correct provider class given provider name
        messaging_provider = messaging_providers.get(provider_name)
        if not messaging_provider:
            raise ValueError(f"Unsupported message provider: {provider_name}")

        # Build message & context
        message = messaging_provider.receive_message(request_body)
        context = context_factory.get_context_from_message(message)

        # Handle return cases
        handle_return_cases(message, context, database_manager, messaging_provider)

        # Create Response Task
        task = ResponseTask(
            context=context,
            messaging_provider=messaging_provider,
            scheduled_for=datetime.now() + timedelta(seconds=0),
            message=message,
        )

        # Handle logging
        insert_and_log_user_message(message, context, database_manager)

        # if cancel_manager.newer_message_found(context.room.id, task.id):
        #     return

        result = agent.process_chat_task(task)

    except Exception as e:
        # if task.context.room.id and task.id:
        #     cancel_manager.remove_task(task.context.room.id, task.id)
        msg = discord_manager.log_error(f"room_id={task.context.room.id}")
        logger.exception(msg)


# TODO implement task cancellation.
# def _store_task_to_redis(self, room_id: str, task: ResponseTask):
#     self.redis_manager.set(
#         key=f"{room_id}:{task.id}",
#         value=task.model_dump_json(),
#         expiry=120,  # Assuming delay is 0
#     )


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
