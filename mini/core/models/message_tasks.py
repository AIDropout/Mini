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
    instructions: str = "Remember, you are replying to this person's iMessage."


class ProactiveTask(MessageTask):
    type: MessageTaskType = MessageTaskType.PROACTIVE
    instructions: str = (
        "Remember, you are texting this person using iMessage, and you are starting a conversation by reaching out first in this instance."
    )


class RemindTask(MessageTask):
    pass
