from zootopia.controller.agent.modules.base import AgentModule
from pydantic import BaseModel
from zootopia.manager.llm import LLMManager
from enum import Enum


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
        llm_manager: LLMManager,
        enabled: bool,
        confidence_threshold: Confidence,
        message_input_count: int,
    ):
        self.llm_manager = llm_manager
        self.enabled = enabled
        self.confidence_threshold = confidence_threshold
        self.message_input_count = message_input_count
