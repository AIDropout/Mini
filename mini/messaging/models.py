from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from .telegram.models import TelegramMessage


class MessageProvider(Enum):
    TELEGRAM = "telegram"
    BIRD = "bird"


class MessageType(Enum):
    TEXT = "text"
    FILE = "file"
    TEXT_AND_FILE = "text_and_file"


class TelegramMetadata(BaseModel):
    uid: Union[int, str]
    user_name: Optional[str]
    chat_id: Optional[str]


class BirdMetadata(BaseModel):
    channel_id: str
    phone_number: str


class MiniMessage(BaseModel):
    content: str
    metadata: Union[TelegramMetadata, BirdMetadata]
    provider: MessageProvider
    type: MessageType
    media_urls: List[str] = Field(default_factory=list)
