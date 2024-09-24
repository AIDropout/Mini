import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from mini.core.models.context import Context


# Function for generating unique ID
def generate_uuid() -> str:
    return str(uuid.uuid4())


# Function for generating the current timestamp
def get_current_time() -> datetime:
    return datetime.now()


class BaseTask(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    created_at: datetime = Field(default_factory=get_current_time)
    context: Context
