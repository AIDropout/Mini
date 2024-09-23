from mini.messaging.models import MessagingProviderEnum, MiniMessage
from .base import BaseTask
from datetime import datetime


class ChatTask(BaseTask):
    provider: MessagingProviderEnum


class ResponseTask(ChatTask):
    scheduled_for: datetime
    message: MiniMessage
    instructions: str = "You are texting someone."  # TODO: implement in prompt builder

    class Config:
        arbitrary_types_allowed = True

    def __str__(self) -> str:
        return (
            f"ResponseTask:\n"
            f"  ID: {self.id}\n"
            f"  Created at: {self.created_at}\n"
            f"  Scheduled for: {self.scheduled_for}\n"
            f"  Provider: {self.provider.value}\n"
        )


class ProactiveTask(ChatTask):
    instructions: str = (
        "You are reaching out."  # TODO: Add time context (ex: "you last texted them last night") and implement
    )


class RemindTask(ChatTask):
    pass
