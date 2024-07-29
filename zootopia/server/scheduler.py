import json
import random
from datetime import datetime, timedelta
import asyncio
from typing import Dict, Any

from zootopia.core.logger import logger
from zootopia.context import MessageContextManager, CronContextManager
from zootopia.core.schema import (
    RespondTask,
    MessageTableModel,
    Tables,
    TaskType,
    RemindTask,
    ReviveTask,
)
from zootopia.agent.agent import Agent
from zootopia.server.redis import redis_client
from config.config import config, Config


class BackgroundScheduler:
    def __init__(self, config: Config):
        self.config = config
        self.redis = redis_client

    def _calculate_response_delay(self):
        """Algorithm for agent responsiveness. We can use agent proactivity, spread of recent messages, etc."""
        scenarios = [(0, 0.7), (5, 0.2), (10, 0.08), (15, 0.02)]
        delay, _ = random.choices(scenarios, weights=[s[1] for s in scenarios])[0]
        return delay + random.randint(0, 3)

    def schedule_respond(self, request_body: dict):
        """This is called by /message endpoint"""
        try:
            context = MessageContextManager(self.config, request_body)
            message = context.database.insert(
                Tables.MESSAGES.value,
                MessageTableModel(
                    room_id=context.room.id,
                    from_user=True,
                    content=context.message.content,
                ),
            )
            if message.content:
                delay = self._calculate_response_delay()
                response_time = datetime.now() + timedelta(seconds=delay)
                logger.info(f"🟢 Scheduling bot response in {delay} seconds")
                creation_time = datetime.now()


                task_data = {
                    "type": TaskType.RESPOND.value,
                    "response_time": response_time.isoformat(),
                    "creation_time": creation_time.isoformat(),
                    #TODO: pass in message object instead of full request
                    "original_request": request_body,
                    "room_id": context.room.id,
                    "message": context.message.content,

                }

                # self.redis.zadd(
                #     "scheduled",
                #     {json.dumps(task_data): response_time.timestamp()},
                # )
        except Exception as e:
            logger.exception(f"Error in schedule respond: {e}")
