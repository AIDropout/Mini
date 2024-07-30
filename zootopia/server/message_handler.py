import random
from datetime import datetime, timedelta

from zootopia.core.logger import logger
from zootopia.context import MessageContextManager
from zootopia.core.schema import (
    MessageTableModel,
    Tables,
    TaskType,
)
from zootopia.server.redis import redis_manager
from config.config import Config
from zootopia.server.celery.tasks import process_task


class MessageHandler:
    def __init__(self, config: Config):
        self.config = config
        self.redis = redis_manager.get_client()

    def _calculate_response_delay(self):
        """Algorithm for agent responsiveness. We can use agent proactivity, spread of recent messages, etc."""
        scenarios = [(0, 0.7), (5, 0.2), (10, 0.08), (15, 0.02)]
        delay, _ = random.choices(scenarios, weights=[s[1] for s in scenarios])[0]
        return delay + random.randint(0, 3)

    def schedule_respond(self, request_body: dict):
        """This is called by /message endpoint.

        It calculates a time, then schedules a celery task.
        """
        try:
            context = MessageContextManager(self.config, request_body)
            context.database.insert(
                Tables.MESSAGES.value,
                MessageTableModel(
                    room_id=context.room.id,
                    from_user=True,
                    content=context.message.content,
                ),
            )

            delay = self._calculate_response_delay()
            creation_time = datetime.now()
            response_time = datetime.now() + timedelta(seconds=delay)

            task_data = {
                "type": TaskType.RESPOND.value,
                "response_time": response_time.isoformat(),
                "creation_time": creation_time.isoformat(),
                "original_request": request_body,  # TODO: pass in message object instead of full request
                "room_id": context.room.id,
                "message": context.message.content,
            }

            logger.info(f"🟢 Scheduling bot response in {delay} seconds")
            process_task.apply_async(args=[task_data], eta=response_time)
        except Exception as e:
            logger.exception(f"Error in schedule respond: {e}")
