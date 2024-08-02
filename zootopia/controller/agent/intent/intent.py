from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Any, Type, Optional, TypeVar, Generic
from pydantic import BaseModel
from dataclasses import dataclass
from zootopia.services import LLM
from zootopia.core.config import config


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
    """
    Manages configurations for different intent types.
    """

    def __init__(self, configs: Dict[str, IntentConfig]):
        """
        Initializes with a dictionary of intent configurations.
        """
        self.configs = configs
        self.max_count = max(config.message_count for config in configs.values())

    def get_past_messages(
        self, intent: str, messages: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """
        Retrieves recent messages based on intent configuration.
        """
        config = self.configs.get(intent)
        return messages[-config.message_count :] if config and config.enabled else []

    def is_enabled(self, intent: str) -> bool:
        """
        Checks if the specified intent is enabled.
        """
        config = self.configs.get(intent)
        return config.enabled if config else False

    def get_confidence_threshold(self, intent: str) -> Confidence:
        """
        Gets the confidence threshold for the specified intent.
        """
        config = self.configs.get(intent)
        return config.confidence_threshold if config else Confidence.MEDIUM


@dataclass
class IntentInput(ABC):
    """
    Base class for intent detection input.
    Contains data to be analyzed for intent.
    """

    message: str

    @abstractmethod
    def __repr__(self) -> str:
        pass


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

    approved: bool

    @property
    @abstractmethod
    def message(self) -> str:
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass


I = TypeVar("I", bound="IntentInput")
O = TypeVar("O", bound="IntentOutput")
R = TypeVar("R", bound="IntentResult")


class IntentProcessor(Generic[I, O, R], ABC):
    """
    Abstract base class for processing intents.
    """

    def __init__(self):
        """
        Initializes the LLM for intent processing.
        """
        self.llm = LLM(config.FILTER_LLM)

    @abstractmethod
    def process(
        self,
        input: I,
        max_retries: int = 3,
        confidence_threshold: Optional[Confidence] = None,
    ) -> R:
        """
        Processes the intent input and returns a result.
        """
        pass

    def _generate_llm_response(
        self, system_prompt: str, user_message: str
    ) -> Dict[str, Any]:
        """
        Generates a response from the LLM.
        """
        return self.llm.generate_response(
            messages=[{"role": "user", "content": user_message}],
            system_prompt=system_prompt,
            json_mode=True,
        )

    @abstractmethod
    def _parse_response(
        self,
        response: Dict[str, Any],
        analyzed_data: Any,
        confidence_threshold: Optional[Confidence],
    ) -> R:
        """
        Parses the LLM response into an intent result.
        """
        pass


class IntentFactory:
    """
    Factory for creating and managing IntentProcessor instances.
    """

    _processors: Dict[str, Type[IntentProcessor]] = {}

    @classmethod
    def register(cls, intent_type: str):
        """
        Decorator for registering intent processors.
        """

        def decorator(processor: Type[IntentProcessor]):
            cls._processors[intent_type] = processor
            return processor

        return decorator

    @classmethod
    def create(cls, intent_type: str) -> Optional[IntentProcessor]:
        """
        Creates an instance of the specified intent processor.
        """
        processor_class = cls._processors.get(intent_type)
        return processor_class() if processor_class else None
