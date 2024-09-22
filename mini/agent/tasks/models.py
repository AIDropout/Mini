from datetime import datetime
from pydantic import BaseModel

from mini.messaging.models import MessagingProviderEnum


class MessageTask(BaseModel):
    message_id: str
    created_at: datetime
    scheduled_time: datetime
    provider: MessagingProviderEnum
    request_body: dict

    class Config:
        arbitrary_types_allowed = True

    def __str__(self) -> str:
        return (
            f"MessageTask:\n"
            f"  ID: {self.message_id}\n"
            f"  Created at: {self.created_at}\n"
            f"  Scheduled for: {self.scheduled_time}\n"
            f"  Provider: {self.provider.value}\n"
        )
