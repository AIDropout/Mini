from dataclasses import dataclass
from typing import ClassVar
from zootopia.core.schema import ZootopiaMessage
from enum import Enum

class ChatTaskType(Enum):
    RESPOND = "respond"
    REVIVE = "revive"
    SCHEDULED = "scheduled"

@dataclass
class ChatTask():
    recent_message_count: ClassVar[int] = 10

@dataclass
class RespondChatTask(ChatTask):
    user_message: ZootopiaMessage
    task: ChatTaskType = ChatTaskType.RESPOND
    instructions: str = "Respond to the user via a short text"
    recent_message_count: ClassVar[int] = 10

    @property
    def message(self) -> str:
        return f"Processing user message: {self.user_message.content[:50]}"

    def __str__(self) -> str:
        return (f"\n\nRespondTask:\n"
                f"  Message: {self.message}\n"
                f"  Instructions: {self.instructions}\n"
                f"  Recent message count: {self.recent_message_count}\n")

@dataclass
class ReviveChatTask(ChatTask):
    task: ChatTaskType = ChatTaskType.REVIVE
    instructions: str = "Re-engage the chat since it has been silent for a while."
    recent_message_count: ClassVar[int] = 5

    @property
    def message(self) -> str:
        return "Reviving inactive chat"

    def __str__(self) -> str:
        return (f"\n\nReviveTask:\n"
                f"  Message: {self.message}\n"
                f"  Instructions: {self.instructions}\n"
                f"  Recent message count: {self.recent_message_count}\n")

@dataclass
class ScheduledChatTask(ChatTask):
    task: ChatTaskType = ChatTaskType.SCHEDULED
    instructions: str = "This event was scheduled for this time. Send a message based on it."
    recent_message_count: ClassVar[int] = 5

    @property
    def message(self) -> str:
        return "Executing scheduled task"

    def __str__(self) -> str:
        return (f"\n\nScheduledTask:\n"
                f"  Message: {self.message}\n"
                f"  Instructions: {self.instructions}\n"
                f"  Recent message count: {self.recent_message_count}\n")
