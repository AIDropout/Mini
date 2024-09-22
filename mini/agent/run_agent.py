from datetime import datetime
from celery import shared_task
from config.container import container
from mini.agent.tasks.models import MessageTask
from mini.core.logger import get_logger
from mini.messaging.discord.discord import discord_manager

# from mini.messaging.service import MessagingService


logger = get_logger(__name__)


@shared_task(bind=True, max_retries=2)
def run_agent(self, room_id: str, message_id: str):
    """Function that initializes and runs the agent"""
    logger.info(f"🔴🔴🔴 running at {datetime.now()}")
    redis_manager = container.get_redis_manager()
    messaging_service = container.get_messaging_service()

    try:
        # Getting the scheduled task data from Redis
        task_json = redis_manager.get(f"{room_id}:{message_id}")
        if not task_json:
            logger.error(f"Task {message_id} in room {room_id} not found in Redis")
            return

        # Convert JSON to Task object
        task = MessageTask.model_validate_json(task_json)
        if not task:
            logger.error(f"Failed to initialize task for message {message_id}")
            return

        # Initialize and run the task
        success = process_agent_task(task, messaging_service)
        if not success:
            logger.warning(
                f"Task {message_id} in room {room_id} was not processed successfully"
            )

    except Exception as e:
        msg = discord_manager.log_error(f"message_id={message_id}")
        logger.exception(msg)
        raise self.retry(exc=e)


def process_agent_task(task: MessageTask, messaging_service):
    from mini.messaging.service import MessagingService  # To avoid circular import

    if not isinstance(messaging_service, MessagingService):
        raise TypeError("messaging_service must be an instance of MessagingService")

    """Internal logic for processing an agent task"""
    messaging_provider = messaging_service.providers.get(task.provider)
    if not messaging_provider:
        raise ValueError(f"Unsupported message provider: {task.provider}")

    message, context = messaging_service._process_incoming_message(
        messaging_provider, task.request_body
    )

    # Change generated message id to actual one
    message.id = task.message_id

    if context.room.disabled_by_admin:
        logger.warning(f"Room {context.room.id} disabled. Canceling process.")
        return False

    messaging_provider.set_receiver(context.user.phone_number)
    messaging_provider.set_sender(context.agent.bird_channel_id)

    agent = container.get_agent_controller()
    agent.configure(
        messaging_manager=messaging_provider,
        agent=context.agent,
        user=context.user,
        room=context.room,
    )

    cancel_manager = container.get_cancel_manager()
    if cancel_manager.newer_message_found(context.room.id, task.message_id):
        return False

    success = agent.respond_to_message(message)

    if success:
        logger.info("Agent processing finished successfully.")

    cancel_manager.remove_task(context.room.id, task.message_id)
    return success
