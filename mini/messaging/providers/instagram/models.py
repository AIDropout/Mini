from typing import List, Optional

from pydantic import BaseModel


class Sender(BaseModel):
    id: str


class Recipient(BaseModel):
    id: str


class MessageContent(BaseModel):
    mid: str
    text: Optional[str] = None
    is_echo: Optional[bool] = None


class ReadReceipt(BaseModel):
    mid: str


class MessageEvent(BaseModel):
    sender: Sender
    recipient: Recipient
    timestamp: int
    message: Optional[MessageContent] = None
    read: Optional[ReadReceipt] = None


class Entry(BaseModel):
    id: str
    time: int
    messaging: List[MessageEvent]


class InstagramWebhook(BaseModel):
    object: str
    entry: List[Entry]
