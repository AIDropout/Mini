from enum import Enum

from mini.core.models.message import MiniMessage
from mini.messaging import MessagingProvider

from .base import BaseTask
from datetime import datetime


class ChatTaskType(Enum):
    RESPONSE = "response"
    PROACTIVE = "proactive"
    REMIND = "remind"


class ChatTask(BaseTask):
    messaging_provider: MessagingProvider

    class Config:
        arbitrary_types_allowed = True


class ResponseTask(ChatTask):
    type: ChatTaskType = ChatTaskType.RESPONSE
    scheduled_for: datetime
    message: MiniMessage
    instructions: str = "You are texting someone."  # TODO: implement in prompt builder


class ProactiveTask(ChatTask):
    type: ChatTaskType = ChatTaskType.PROACTIVE
    instructions: str = (
        "You are reaching out."  # TODO: Add time context (ex: "you last texted them last night") and implement
    )


class RemindTask(ChatTask):
    pass
