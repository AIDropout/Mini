import base64
from typing import Dict, List, Optional

import httpx

from mini.controller.agent.modules.base import AgentModule
from mini.core.error import error_handler
from mini.core.event_logger import event_logger as el
from mini.core.logger import logger
from mini.core.schema.tables import Message, Tables
from mini.manager.database import DatabaseManager
from mini.manager.llm import LLMManager


class VisionModule(AgentModule):
    SYSTEM_PROMPT = """You're a texting AI that analyzes images. Keep responses around 3 sentences. Start with a brief overall summary. Describe main elements: subjects, actions, setting, colors. Note unusual features or context if relevant. Be objective and accurate."""

    def __init__(self, database_manager: DatabaseManager, llm_manager: LLMManager):
        super().__init__(database_manager)
        self.llm_manager = llm_manager

    @error_handler("VisionModule")
    def handle_images(self, urls: List[str]) -> str:
        """
        Receives a list of urls hosted on AWS.
        Passes each image through Vision model.
        Returns a str of the image context.
        """
        generation = self.llm_manager.describe_images(
            system_prompt=self.SYSTEM_PROMPT, image_urls=urls
        )
        logger.info(f"🟢 Generated image description: {generation}")

        inserted_message = self.database_manager.insert(
            Tables.MESSAGES,
            Message(
                room_id=self.room.id,
                sender_id=self.user.id,
                content=generation,
            ),
        )

        return generation
