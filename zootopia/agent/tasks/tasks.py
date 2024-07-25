from dataclasses import dataclass
from typing import ClassVar
from zootopia.core.schema import ActionType, RoomTableModel, ZootopiaMessage

# TODO: Add possible actions
@dataclass
class ChatTask():
    status: ClassVar[str] = ''

@dataclass
class UserMessageTask(ChatTask):
    user_message: ZootopiaMessage

    instructions: str = "Respond to the user via a short text"
    recent_message_count: int = 10

@dataclass
class ChatReviverTask(ChatTask):
    instructions: str = "Re-engage the chat since it has been silent for a while."
    recent_message_count: int = 5

@dataclass
class ScheduledTask(ChatTask):
    instructions: str = "This event was scheduled for this time. Send a message based on it."
    recent_message_count: int = 5
