import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from mini.core.models.context import Context


class BaseTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    context: Context
