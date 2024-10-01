from datetime import datetime
from typing import Dict, List

from mini.core.enums import MessageTaskType
from mini.core.models.base_task import BaseTask
from mini.messaging.providers import MessagingProvider


class MessageTask(BaseTask):
    messaging_provider: MessagingProvider
    recent_messages: List[Dict[str, str]]

    class Config:
        arbitrary_types_allowed = True


class ResponseTask(MessageTask):
    type: MessageTaskType = MessageTaskType.RESPONSE
    scheduled_for: datetime
    instructions: str = "You are replying to someone's message."


class ProactiveTask(MessageTask):
    type: MessageTaskType = MessageTaskType.PROACTIVE
    instructions: str = "You are starting a conversation by reaching out."


class RemindTask(MessageTask):
    pass
