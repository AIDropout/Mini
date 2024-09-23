import uuid
from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, Field


# GENERAL
class MessagingProviderEnum(Enum):
    TELEGRAM = "telegram"
    BIRD = "bird"
    INSTAGRAM = "instagram"


class ResponseTypeEnum(Enum):
    PROACTIVE = "proactive"
    RESPOND = "respond"


class MessageType(Enum):
    TEXT = "text"
    FILE = "file"
    TEXT_AND_FILE = "text_and_file"


# IDENTITY METADATA
class TelegramMetadata(BaseModel):
    uid: Union[int, str]
    user_name: Optional[str]
    chat_id: Optional[str]


class BirdMetadata(BaseModel):
    channel_id: str
    phone_number: str


class InstagramMetadata(BaseModel):
    sender_id: str
    recipient_id: str


# MINIMESSAGE
class MiniMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    metadata: Union[TelegramMetadata, BirdMetadata, InstagramMetadata]
    provider: MessagingProviderEnum
    type: MessageType
    media_urls: List[str] = Field(default_factory=list)
