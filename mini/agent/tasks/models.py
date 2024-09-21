from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from mini.messaging.models import MiniMessage
from mini.messaging.context import Context


class BaseTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    scheduled_for: datetime
    created_at: datetime = Field(default_factory=datetime.now)
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
    user_message: MiniMessage
    context: Context
    instructions: str = Field(default="Respond to the user via a short text")
    recent_message_count: int = Field(default=10)

    @property
    def task_message(self) -> str:
        return f"Processing user message: {self.user_message.content[:50]}"
