from pydantic import BaseModel
from typing import Union
from mini.core.models.context import Context
from mini.messaging.tasks.models import ChatTask, ResponseTask, ProactiveTask


class Task(BaseModel):
    context: Context
    task: Union[
        ChatTask, ResponseTask, ProactiveTask
    ]  # Add future tasks like BrowseWebTask, etc.
