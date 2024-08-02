"""Note: Actions are currently not implemented. None of the action files are being used."""

from typing import List, Dict, Optional
from zootopia.core.schema import MessageTableModel
from zootopia.core.logger import logger
from zootopia.services import LLM
from zootopia.core.config import config
from zootopia.services import MessageProvider
import random
import asyncio
from typing import List
from zootopia.utils.utils import DynamicResponseModel

from pydantic import BaseModel, Field


class IntentFilters(BaseModel):
    title: str
    description: str


class IntentConfig(BaseModel):
    filters: List[IntentFilters]


class LLMResponseStructure(BaseModel):
    intent: dict = Field(
        "{ (dict) A dictionary of intents as keys and their confidence levels "
        "('high', 'medium', 'low') as values. Only include relavent intent keys. "
        "It is possible no intents exist, making this an empty dictionary. }"
    )


class ActionManager:
    def __init__(self, messaging_service: MessageProvider) -> None:
        self.llm = LLM(config.ACTION_MANAGER_LLM)
        self.messaging_service = messaging_service

    def generate_message(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str],
    ) -> Optional[str]:
        msg = self.llm.generate_response(messages, system_prompt)
        return msg

    async def handle_message_send(self, msg: str) -> None:
        messages = msg.split("|")

        for i, message in enumerate(messages):
            await self.messaging_service.send_message(message.strip())

            if i < len(messages) - 1:  # Don't delay after the last message
                delay = random.uniform(0, 10)  # Random delay between 0 and 10 seconds
                await asyncio.sleep(delay)

    def should_respond(self, recent_messages: List[MessageTableModel]) -> bool:
        """LLM looks at recent messages and determines if it should respond or not."""

        template = """
        Your task is to analyze the given text and determine if there's a need to schedule a response or reminder in the future.


        """

        # Format recent messages

        response_format = {}

        system_prompt = template.format(response_format=response_format)

        json_output = self.llm.generate_response(
            messages=[{"role": "user", "content": "Determine."}],
            system_prompt=system_prompt,
        )