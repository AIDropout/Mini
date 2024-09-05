import asyncio
import random
from typing import Dict, List, Optional

from mini.controller.agent.modules.base import AgentModule
from mini.core.error import error_handler
from mini.core.event_logger import event_logger as el
from mini.core.logger import get_logger
from mini.manager.llm import LLMManager
from mini.manager.messaging import MessagingManager

logger = get_logger(__name__)


class ActionModule(AgentModule):
    def __init__(self, llm_manager: LLMManager):
        self.llm_manager = llm_manager
        self.messaging_manager = None

    def set_messaging_manager(self, messaging_manager: MessagingManager) -> None:
        self.messaging_manager = messaging_manager

    @error_handler("ActionManager")
    def generate_message(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str],
    ) -> str:
        msg = self.llm_manager.generate_response(messages, system_prompt)
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
            except Exception as e:
                logger.error(str(e))
                overall_success = False

        return overall_success
