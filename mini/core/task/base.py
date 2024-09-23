from pydantic import BaseModel
from mini.core.models.context import Context

class BaseTask(BaseModel):
    id: str
    context: Context
