from enum import Enum
from typing import List

from pydantic import BaseModel, Field

from enum import Enum


class Intents(Enum):
    USER_SIGNUP = "USER_SIGNUP"
    AUTH_GOOGLE = "AUTH_GOOGLE"
    SAVE_FILE = "SAVE_FILE"
    SAVE_DATA = "SAVE_DATA"
    ANSWER_QUERY = "ANSWER_QUERY"

class Confidence(Enum):
    LOW = "low"
    MID = "medium"
    HIGH = "high"

    def __ge__(self, other):
        order = [Confidence.LOW, Confidence.MID, Confidence.HIGH]
        return order.index(self) >= order.index(other)


class IntentFilters(BaseModel):
    title: str
    description: str


class IntentConfig(BaseModel):
    # llm_config: LLMConfig
    filters: List[IntentFilters]


class LLMResponseStructure(BaseModel):
    intent: dict = Field(
        "{ (dict) A dictionary of intents as keys and their confidence levels "
        f"('{Confidence.LOW.value}', '{Confidence.MID.value}', '{Confidence.HIGH.value}') as values. "
        "Only include relavent intent keys. "
        "It is possible no intents exist, making this an empty dictionary. }"
    )
