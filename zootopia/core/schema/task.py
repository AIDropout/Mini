from dataclasses import dataclass
from typing import ClassVar
from zootopia.core.schema import ZootopiaMessage
from enum import Enum


class TaskType(Enum):
    RESPOND = "respond"
    REMIND = "remind"
    REVIVE = "revive"


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
