from enum import Enum
from typing import List, Optional, Union
from pydantic import BaseModel, Field


# GENERAL
class MessagingProviderEnum(Enum):
    TELEGRAM = "telegram"
    BIRD = "bird"
    INSTAGRAM = "instagram"


class MessageType(Enum):
    TEXT = "text"
    FILE = "file"
    TEXT_AND_FILE = "text_and_file"

# Our version of sender & receiver
class MiniMessageMetadata(BaseModel):
    sender_id: str
    receiver_id: str

# MINIMESSAGE
class MiniMessage(BaseModel):
    content: str
    metadata: MiniMessageMetadata
    provider: MessagingProviderEnum
    type: MessageType
    media_urls: List[str] = Field(default_factory=list)
