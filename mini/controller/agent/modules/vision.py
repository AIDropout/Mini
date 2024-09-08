from typing import List

from mini.controller.agent.modules.base import AgentModule
from mini.core.exceptions import VisionError
from mini.core.logger import get_logger
from mini.manager.database import DatabaseManager
from mini.manager.llm import LLMManager

logger = get_logger(__name__)


class VisionModule(AgentModule):
    SYSTEM_PROMPT = """You're a texting AI that analyzes images. Keep responses around 3 sentences. Start with a brief overall summary. Describe main elements: subjects, actions, setting, colors. Note unusual features or context if relevant. Be objective and accurate."""

    def __init__(self, database_manager: DatabaseManager, llm_manager: LLMManager):
        super().__init__(database_manager)
        self.llm_manager = llm_manager

    def handle_images(self, urls: List[str]) -> str:
        """
        Receives a list of urls hosted on AWS.
        Passes each image through Vision model.
        Returns a str of the image context.
        """
        try:
            generation = self.llm_manager.describe_images(
                system_prompt=self.SYSTEM_PROMPT, image_urls=urls
            )
            logger.info(f"🟢 Generated image description: {generation}")
            return generation
        except Exception as e:
            raise VisionError("Error in generating an image description.") from e
