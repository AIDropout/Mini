from celery import shared_task
from zootopia.controller.context import MessageContextManager, CronContextManager
from zootopia.core.schema import TaskType
from zootopia.controller.agent.agent import Agent
from zootopia.core.config import config
from zootopia.core.logger import logger
import asyncio
from datetime import datetime
from zootopia.server.cancel import cancel_existing_task
from dataclasses import dataclass
from typing import ClassVar
from zootopia.core.schema import ZootopiaMessage



@shared_task(bind=True, max_retries=2)
def process_task(self, data: dict):
    logger.info(f"🔴🔴🔴 running at {datetime.now()}")
    try:
        context, task = create_task_and_context(data)
        if not context or not task:
            logger.warning(f"Invalid task data: {data}")
            return

        agent = Agent.from_context(context)
        success = asyncio.run(agent.handle_chat_task(task))

        if not success:
            cancel_existing_task(context.room.id)
        else:
            raise Exception("Task processing failed")
    except Exception as exc:
        logger.error(f"Error processing task: {exc}")
        self.retry(exc=exc, countdown=60)


def create_task_and_context(data: dict):
    task_type = data["type"]
    if task_type == TaskType.RESPOND.value:
        context = MessageContextManager(data["original_request"])
        task = RespondTask(context.message)
    elif task_type == TaskType.REMIND.value:
        context = CronContextManager(data["room_id"])
        task = RemindTask()
    elif task_type == TaskType.REVIVE.value:
        context = None
        task = ReviveTask()
    else:
        logger.warning(f"Unknown task type: {task_type}")
        return None, None
    return context, task


@dataclass
class Task:
    recent_message_count: ClassVar[int] = 10


@dataclass
class RespondTask(Task):
    user_message: ZootopiaMessage
    type: TaskType = TaskType.RESPOND
    instructions: str = "Respond to the user via a short text"
    recent_message_count: ClassVar[int] = 10

    @property
    def message(self) -> str:
        return f"Processing user message: {self.user_message.content[:50]}"

    def __str__(self) -> str:
        return (
            f"\n\nRespondTask:\n"
            f"  Message: {self.message}\n"
            f"  Instructions: {self.instructions}\n"
            f"  Recent message count: {self.recent_message_count}\n"
        )


@dataclass
class RemindTask(Task):
    name: str
    type: TaskType = TaskType.REMIND
    instructions: str = (
        "This event was scheduled for this time. Send a message based on it."
    )
    recent_message_count: ClassVar[int] = 5

    @property
    def message(self) -> str:
        return "Executing remind task"

    def __str__(self) -> str:
        return (
            f"\n\nRemindTask:\n"
            f"  Message: {self.message}\n"
            f"  Instructions: {self.instructions}\n"
            f"  Recent message count: {self.recent_message_count}\n"
        )


@dataclass
class ReviveTask(Task):
    type: TaskType = TaskType.REVIVE
    instructions: str = "Re-engage the chat since it has been silent for a while."
    recent_message_count: ClassVar[int] = 5

    @property
    def message(self) -> str:
        return "Reviving inactive chat"

    def __str__(self) -> str:
        return (
            f"\n\nReviveTask:\n"
            f"  Message: {self.message}\n"
            f"  Instructions: {self.instructions}\n"
            f"  Recent message count: {self.recent_message_count}\n"
        )
