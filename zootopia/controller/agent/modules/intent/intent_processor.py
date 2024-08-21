from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Any, Type, Optional, TypeVar, Generic
from dataclasses import dataclass
from zootopia.manager.llm import LLMManager
from config.config import config


class Confidence(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

    def __ge__(self, other: "Confidence") -> bool:
        order = ["LOW", "MEDIUM", "HIGH"]
        return order.index(self) >= order.index(other)


@dataclass
class IntentInput(ABC):
    """
    Base class for intent detection input.
    Contains data to be analyzed for intent.
    """

    message: str


@dataclass
class IntentOutput(ABC):
    """
    Base class for raw intent detection output.
    Defines structure of LLM or service response.
    """

    confidence: Confidence
    reason: str


@dataclass
class IntentResult(ABC):
    """
    Base class for processed intent detection result.
    Contains final, validated intent information.
    """

    approved: bool
    reason: str


class IntentProcessor(ABC):
    def __init__(self):
        self.llm = LLMManager(config.FILTER_LLM)

    @abstractmethod
    def process(
        self, input: IntentInput, confidence_threshold: Optional[Confidence] = None
    ) -> IntentResult:
        pass

    def _generate_llm_response(
        self, system_prompt: str, user_message: str
    ) -> Dict[str, Any]:
        return self.llm.generate_response(
            messages=[{"role": "user", "content": user_message}],
            system_prompt=system_prompt,
            json_mode=True,
        )
