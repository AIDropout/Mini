"""Note: Actions are currently not implemented. None of the action files are being used."""

from typing import List, Dict, Optional, Tuple, Any
from zootopia.core.schema import MessageTableModel
from zootopia.core.logger import logger
from zootopia.services import LLM
from zootopia.core.config import config
from zootopia.services import MessageProvider
import random
import asyncio
from typing import List
from zootopia.core.event_logger import event_logger as el
from datetime import datetime

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

    async def handle_message_send(self, msg: str) -> Tuple[bool, str]:
        """
        Handle sending of potentially multi-part messages.

        Args:
            msg (str): The message to send, potentially containing multiple parts separated by '|'.

        Returns:
            Tuple[bool, str]: Overall success status and a log message string.
        """
        messages = msg.split("|")
        overall_success = True
        log_messages = []

        for i, message in enumerate(messages):
            try:
                success, details = await self.messaging_service.send_message(message.strip())
                overall_success = overall_success and success
                
                log_message = f"Message '{message[:20]}...' {'sent successfully' if success else 'failed to send'}"
                log_messages.append(log_message)

                if i < len(messages) - 1:
                    await asyncio.sleep(random.uniform(0, 10))
            except Exception as e:
                log_messages.append(f"Error sending message '{message[:20]}...': {str(e)}")
                overall_success = False

        return overall_success, " | ".join(log_messages)