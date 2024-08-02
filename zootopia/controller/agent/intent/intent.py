from dataclasses import dataclass
from abc import ABC

@dataclass
class IntentInput(ABC):
    """
    Base class for intent detection input.
    Contains data to be analyzed for intent.
    """
    pass

@dataclass
class IntentOutput(ABC):
    """
    Base class for raw intent detection output.
    Defines structure of LLM or service response.
    """
    pass

@dataclass
class IntentResult(ABC):
    """
    Base class for processed intent detection result.
    Contains final, validated intent information.
    """
    pass