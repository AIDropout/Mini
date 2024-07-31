"""Note: Actions are currently not implemented. None of the action files are being used."""

from typing import List, Dict, Optional
from zootopia.core.schema import Action, ActionType, ActionResult
from zootopia.core.logger import logger
from zootopia.services import LLM
from zootopia.core.config import config
from zootopia.services import MessageProvider


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

    async def send_message(self, msg: str) -> None:
        await self.messaging_service.send_message(msg)
