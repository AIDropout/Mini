from pydantic import BaseModel
from typing import Union
from mini.core.models.context import Context
from mini.core.models.message_tasks import MessageTask, ResponseTask, ProactiveTask


class Task(BaseModel):
    context: Context
    task: Union[
        MessageTask, ResponseTask, ProactiveTask
    ]  # Add future tasks like BrowseWebTask, etc.
