from enum import Enum

from pydantic import BaseModel

from mini.controller.agent.modules.base import AgentModule
from mini.manager.llm import LLMService


class Confidence(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

    def __ge__(self, other: "Confidence") -> bool:
        order = ["LOW", "MEDIUM", "HIGH"]
        return order.index(self) >= order.index(other)


class IntentConfig(BaseModel):
    message_input_count: int
    confidence_threshold: Confidence
    enabled: bool = True


class IntentDetector(AgentModule):
    def __init__(
        self,
        llm_manager: LLMService,
        enabled: bool,
        message_input_count: int,
        confidence_threshold: Confidence = Confidence.MEDIUM,
    ):
        self.llm_manager = llm_manager
        self.enabled = enabled
        self.confidence_threshold = confidence_threshold
        self.message_input_count = message_input_count
