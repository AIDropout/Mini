from dataclasses import dataclass
from abc import ABC
from enum import Enum
from typing import Dict, List
from pydantic import BaseModel, Field


class Confidence(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

    def __ge__(self, other: "Confidence") -> bool:
        order = ["LOW", "MEDIUM", "HIGH"]
        return order.index(self.value) >= order.index(other.value)


class IntentConfig(BaseModel):
    message_count: int
    confidence_threshold: Confidence
    enabled: bool = True

class IntentConfigManager:
    def __init__(self, configs: Dict[str, IntentConfig]):
        self.configs = configs
        self.max_count = max(config.message_count for config in configs.values())

    def get_past_messages(self, intent: str, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        config = self.configs.get(intent)
        if not config or not config.enabled:
            return []
        return messages[-config.message_count:]

    def is_enabled(self, intent: str) -> bool:
        config = self.configs.get(intent)
        return config.enabled if config else False

    def get_confidence_threshold(self, intent: str) -> Confidence:
        config = self.configs.get(intent)
        return config.confidence_threshold if config else Confidence.MEDIUM



@dataclass
class IntentInput(ABC):
    """
    Base class for intent detection input.
    Contains data to be analyzed for intent.
    """

    new_message: str


@dataclass
class IntentOutput(ABC):
    """
    Base class for raw intent detection output.
    Defines structure of LLM or service response.
    """

    confidence: Confidence


@dataclass
class IntentResult(ABC):
    """
    Base class for processed intent detection result.
    Contains final, validated intent information.
    """

    confidence: Confidence
    approved: bool
