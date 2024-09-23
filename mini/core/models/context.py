from mini.database.models import User, Agent, Room
from typing import Optional
from dataclasses import dataclass

@dataclass
class Context:
    user: Optional[User] = None
    agent: Optional[Agent] = None
    room: Optional[Room] = None