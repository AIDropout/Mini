from enum import Enum
from typing import List
from pydantic import BaseModel, Field

from mini.core.enums import MessagingProviderType


class MessageType(Enum):
    TEXT = "text"
    FILE = "file"
    TEXT_AND_FILE = "text_and_file"


# Our version of sender & receiver
class MiniMessageMetadata(BaseModel):
    sender_id: str
    receiver_id: str


class MiniMessage(BaseModel):
    content: str
    metadata: MiniMessageMetadata
    provider: MessagingProviderType
    type: MessageType
    media_urls: List[str] = Field(default_factory=list)
