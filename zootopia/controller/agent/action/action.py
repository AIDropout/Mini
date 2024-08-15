"""Note: Actions are currently not implemented. None of the action files are being used."""

from typing import List, Dict, Optional, Tuple, Any
from zootopia.core.schema import Message
from zootopia.core.logger import logger
from zootopia.manager.llm import LLMManager
from zootopia.manager.messaging import MessagingManager
from config.config import config
import random
import asyncio
from typing import List
from zootopia.controller.agent.event_logger import event_logger as el
from datetime import datetime
from zootopia.core.error import error_handler


class ActionManager:
    def __init__(self, messaging_manager: MessagingManager) -> None:
        self.llm = LLMManager(config.ACTION_MANAGER_LLM)
        self.messaging_manager = messaging_manager

    @error_handler("ActionManager")
    def generate_message(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str],
    ) -> str:
        msg = self.llm.generate_response(messages, system_prompt)
        return msg

    @error_handler("ActionManager")
    async def handle_message_send(self, msg: str) -> bool:
        """
        Handle sending of potentially multi-part messages.

        Args:
            msg (str): The message to send, potentially containing multiple parts separated by '|'.

        Returns:
            bool: Overall success status.
        """
        messages = msg.split("|")
        overall_success = True

        for i, message in enumerate(messages):
            try:
                success, _ = await self.messaging_manager.send_message(message.strip())
                overall_success = overall_success and success

                if i < len(messages) - 1:
                    await asyncio.sleep(random.uniform(0, 10))
            except Exception:
                overall_success = False

        return overall_success
