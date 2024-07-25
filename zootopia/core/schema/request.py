from pydantic import BaseModel
from typing import Optional, Tuple

class SignupRequestBase(BaseModel):
    agent_id: int
    user_phone: str
    birthday: Optional[str] = None    