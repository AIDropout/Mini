from datetime import datetime

from celery import shared_task

from config.container import container
from mini.core.logger import get_logger
from mini.core.task.chat import ResponseTask
from mini.messaging.discord.discord import discord_manager

logger = get_logger(__name__)


@shared_task(bind=True, max_retries=2)
def run_agent(self, room_id: str, task_id: str):
    """Function that initializes and runs the agent"""
    logger.info(f"🔴🔴🔴 running at {datetime.now()}")
    redis_manager = container.get_redis_manager()

    try:
        # Getting the scheduled task data from Redis
        task_json = redis_manager.get(f"{room_id}:{task_id}")
        if not task_json:
            raise KeyError(f"Task {task_id} in room {room_id} not found in Redis")

        # Convert JSON to Task object
        task = ResponseTask.model_validate_json(task_json)
        if not task:
            logger.error(f"Failed to initialize task for message {task_id}")
            return

        # Initialize messaging provider
        messaging_service = container.get_messaging_service()
        messaging_provider = messaging_service.providers.get(task.provider)
        if not messaging_provider:
            raise ValueError(f"Unsupported message provider: {task.provider}")
        messaging_provider.set_receiver(task.message.metadata.receiver_id)
        messaging_provider.set_sender(task.message.metadata.sender_id)

        # Run agent
        agent = container.get_agent_controller()
        success = agent.handle_chat_task(task, messaging_provider)

        if not success:
            logger.warning(
                f"Task {task_id} in room {room_id} was not processed successfully"
            )

    except Exception as e:
        msg = discord_manager.log_error(f"task_id={task_id}")
        logger.exception(msg)
        raise self.retry(exc=e)
