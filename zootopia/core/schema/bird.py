from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum

class BirdFile(BaseModel):
    mediaUrl: str

class BirdFileContent(BaseModel):
    text: Optional[str] = None
    files: List[BirdFile]
    metadata: Dict[str, str] = Field(default_factory=dict)

class BirdTextContent(BaseModel):
    text: str

class BirdBody(BaseModel):
    type: str
    text: Optional[BirdTextContent] = None
    file: Optional[BirdFileContent] = None

class BirdContact(BaseModel):
    id: str
    identifierKey: str
    identifierValue: str

class BirdSender(BaseModel):
    contact: BirdContact

class BirdReceiver(BaseModel):
    connector: Dict[str, str]

class BirdMeta(BaseModel):
    extraInformation: Dict[str, str]

class BirdMessage(BaseModel):
    id: str
    channelId: str
    sender: BirdSender
    receiver: BirdReceiver
    body: BirdBody
    meta: BirdMeta
    reference: str
    parts: List[Dict[str, str]]
    status: str
    reason: str
    direction: str
    chargeableUnits: int
    lastStatusAt: str
    createdAt: str
    updatedAt: str

class BirdRequest(BaseModel):
    service: str
    event: str
    payload: BirdMessage