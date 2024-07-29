"""This class, specifically the run method, is what's running continously"""

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
from config.config import Config


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
                self._log_diagnosis()
                now = datetime.now().timestamp()
                due_tasks = self.redis.zrangebyscore("scheduled", 0, now)

                for t in due_tasks:
                    # Lock the task so another gunicorn worker doesn't run it simultaneously
                    lock = self.redis.lock(f"task_lock:{t}", blocking_timeout=5)
                    if lock.acquire(blocking=False):
                        try:
                            data = json.loads(t)
                            task_type = data["type"]
                            logger.info(f"Processing scheduled task: {task_type}")

                            context, task = self.create_task_and_context(data)
                            if task is None or context is None:
                                self.redis.zrem("scheduled", t)
                                continue

                            agent = Agent.from_config(self.config, context)
                            success = await agent.handle_chat_task(task)

                            if success:
                                self.redis.zrem("scheduled", t)

                        finally:
                            lock.release()
                    else:
                        # Another worker is processing this task, skip it
                        pass

                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error in background task: {e}")
                # Remove the problematic task from the schedule
                # TODO: better error handling, design re-trying/re-scheduling
                self.redis.zrem("scheduled", t)

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

    def create_task_and_context(self, data):
        task_type = data["type"]
        if task_type == TaskType.RESPOND.value:
            context = MessageContextManager(self.config, data["original_request"])
            task = RespondTask(context.message)
        elif task_type == TaskType.REMIND.value:
            context = CronContextManager(self.config, data["room_id"])
            task = RemindTask()
        elif task_type == TaskType.REVIVE.value:
            context = None
            task = ReviveTask()
        else:
            logger.warning(f"Unknown task type: {task_type}")
            return None, None
        return context, task
