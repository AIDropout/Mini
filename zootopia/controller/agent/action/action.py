"""Note: Actions are currently not implemented. None of the action files are being used."""

from typing import List, Dict, Optional
from zootopia.core.schema import Action, ActionType, ActionResult
from zootopia.core.logger import logger
from zootopia.services import LLM
from zootopia.core.config import config
from zootopia.services import MessageProvider
import random
import asyncio
from typing import List

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

    def detect_intent(self, text: str):

        template = """
        Your task is to analyze the given text and determine if there's a need to schedule a response or reminder in the future.

        If a scheduling intent is detected, respond with a JSON object containing the following information:
        {
            "intent": "schedule",
            "name": "Tell John happy birthday",
            "run_at": "YYYY-MM-DD HH:MM:SS"
        }

        If no scheduling intent is detected, respond with an empty JSON object:
        {}

        Ensure that the "run_at" field is a valid date and time in the future, formatted as specified.

        Example:
        User input: "Remind me to call John tomorrow at 2 PM"
        Response:
        {
            "intent": "schedule",
            "name": "Call John",
            "run_at": "2024-08-01 14:00:00"
        }

        Only include the JSON object in your response, without any additional text.
        """

        response_format = {}

        system_prompt = template.format(response_format=response_format)

        json_output = self.llm.generate_response(
            messages=[{"role": "user", "content": "Verify the message."}],
            system_prompt=system_prompt,
            json_mode=True,
        )

