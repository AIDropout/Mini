from dataclasses import dataclass
from abc import ABC


@dataclass
class ConfidenceScore:
    score: int

    def __post_init__(self):
        if not (0 <= self.score <= 100):
            raise ValueError("Confidence score must be between 0 and 100")

    def is_confident(self, threshold: "ConfidenceScore") -> bool:
        return self.score >= threshold

    def __repr__(self) -> str:
        return f"ConfidenceScore(score={self.score})"


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
