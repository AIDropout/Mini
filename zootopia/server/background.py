import json
import asyncio
from datetime import datetime
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
from zootopia.server.celery import celery_app
from config.config import Config
from zootopia.server.tasks import process_task

class BackgroundRunner:
    def __init__(self, config: Config):
        self.config = config
        self.redis = redis_client

    async def run(self):
        """
        Continuously processes scheduled tasks stored in Redis:
        - Retrieves due tasks based on current timestamp
        - Creates and executes tasks using configured agents
        - Removes completed tasks from Redis
        - Implements error handling and periodic execution
        """
        while True:
            try:
                now = datetime.now().timestamp()
                due_tasks = self.redis.zrangebyscore("scheduled", 0, now)
                for task in due_tasks:
                    await process_task.delay(task)
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error in background task: {e}")
                await asyncio.sleep(1)

    def _log_diagnosis(self):
        """Prints scheduling info. Feel free to change this however"""
        now = datetime.now()
        scheduled_tasks = self.redis.zrange("scheduled", 0, -1, withscores=True)

        print(f"\n🪻 Scheduled tasks at {now.strftime('%H:%M:%S')}:")
        for i, (task, score) in enumerate(scheduled_tasks[:5]):
            task_data = json.loads(task.decode("utf-8"))
            scheduled_time = datetime.fromtimestamp(score)
            time_until_due = scheduled_time - now

            print(
                f"{i+1}. Time: {scheduled_time.strftime('%H:%M:%S')}, "
                f"Due in: {time_until_due.total_seconds():.1f}s"
            )

        if len(scheduled_tasks) > 5:
            print(f"... and {len(scheduled_tasks) - 5} more tasks")
        elif len(scheduled_tasks) == 0:
            print("0 tasks scheduled.")
