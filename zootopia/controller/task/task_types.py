from pydantic import BaseModel, Field
from datetime import datetime
from uuid import uuid4
from zootopia.core.schema.task import TaskType
from zootopia.core.schema.message import ZootopiaMessage
from zootopia.service.context_factory import Context
from typing import Optional

class BaseTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    scheduled_for: datetime
    created_at: datetime = Field(default_factory=datetime.now)
    type: TaskType
    instructions: str
    recent_message_count: int

    class Config:
        arbitrary_types_allowed = True

    @property
    def task_message(self) -> str:
        raise NotImplementedError("Subclasses must implement task_message")

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f"  Recent message count: {self.recent_message_count}\n"
        )

class RespondTask(BaseTask):
    user_message: ZootopiaMessage
    context: Context
    type: TaskType = Field(default=TaskType.RESPOND)
    instructions: str = Field(default="Respond to the user via a short text")
    recent_message_count: int = Field(default=10)

    @property
    def task_message(self) -> str:
        return f"Processing user message: {self.user_message.content[:50]}"

class RemindTask(BaseTask):
    name: str
    type: TaskType = Field(default=TaskType.REMIND)
    instructions: str = Field(default="This event was scheduled for this time. Send a message based on it.")
    recent_message_count: int = Field(default=5)

    @property
    def task_message(self) -> str:
        return f"Executing remind task: {self.name}"

class ReviveTask(BaseTask):
    type: TaskType = Field(default=TaskType.REVIVE)
    instructions: str = Field(default="Re-engage the chat since it has been silent for a while.")
    recent_message_count: int = Field(default=5)

    @property
    def task_message(self) -> str:
        return "Reviving inactive chat"