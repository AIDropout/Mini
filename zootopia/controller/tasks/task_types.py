from zootopia.core.schema import TaskType
from dataclasses import dataclass
from typing import ClassVar
from zootopia.core.schema import ZootopiaMessage
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional
from abc import ABC, abstractmethod


@dataclass
class BaseTask(ABC):
    room_id: ClassVar[int]
    type: ClassVar[TaskType]
    instructions: ClassVar[str]
    recent_message_count: ClassVar[int] = 10

    @property
    @abstractmethod
    def message(self) -> str:
        pass

    def __str__(self) -> str:
        return (
            f"\n\n{self.__class__.__name__}:\n"
            f"  Type: {self.type.value}\n"
            f"  Message: {self.message}\n"
            f"  Instructions: {self.instructions}\n"
            f"  Recent message count: {self.recent_message_count}\n"
        )


@dataclass
class RespondTask(BaseTask):
    user_message: ZootopiaMessage
    room_id: int
    type: ClassVar[TaskType] = TaskType.RESPOND
    instructions: ClassVar[str] = "Respond to the user via a short text"
    recent_message_count: ClassVar[int] = 10

    @property
    def message(self) -> str:
        return f"Processing user message: {self.user_message.content[:50]}"


@dataclass
class RemindTask(BaseTask):
    name: str
    type: ClassVar[TaskType] = TaskType.REMIND
    instructions: ClassVar[str] = (
        "This event was scheduled for this time. Send a message based on it."
    )
    recent_message_count: ClassVar[int] = 5

    @property
    def message(self) -> str:
        return f"Executing remind task: {self.name}"


@dataclass
class ReviveTask(BaseTask):
    room_id: int
    type: ClassVar[TaskType] = TaskType.REVIVE
    instructions: ClassVar[str] = (
        "Re-engage the chat since it has been silent for a while."
    )
    recent_message_count: ClassVar[int] = 5

    @property
    def message(self) -> str:
        return "Reviving inactive chat"


@dataclass
class ScheduledTaskInfo:
    task: BaseTask
    delay: int
    original_request: Optional[dict] = None
    creation_time: datetime = field(default_factory=datetime.now)

    @property
    def response_time(self) -> datetime:
        return self.creation_time + timedelta(seconds=self.delay)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.task.type.value,
            "response_time": self.response_time.isoformat(),
            "creation_time": self.creation_time.isoformat(),
            "original_request": self.original_request,
            "room_id": self.task.room_id,
            "message": self.task.message,
            "instructions": self.task.instructions,
        }
