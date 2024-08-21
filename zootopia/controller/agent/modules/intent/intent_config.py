from typing import Dict, List
from pydantic import BaseModel
from zootopia.controller.agent.modules.intent.intent_processor import Confidence
from zootopia.core.schema.intent import IntentType


class IntentConfig(BaseModel):
    message_count: int
    confidence_threshold: Confidence
    enabled: bool = True


INTENT_CONFIGS = {
    IntentType.FILTER: IntentConfig(
        message_count=5, confidence_threshold=Confidence.HIGH, enabled=True
    ),
    IntentType.SCHEDULE: IntentConfig(
        message_count=3, confidence_threshold=Confidence.MEDIUM, enabled=False
    ),
    IntentType.SKIP: IntentConfig(
        message_count=3, confidence_threshold=Confidence.HIGH, enabled=True
    ),
}


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
