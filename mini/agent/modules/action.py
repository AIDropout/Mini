from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel

from mini.agent.modules.base import AgentModule
from mini.core.logger import get_logger
from mini.database.models import Tables
from mini.llm import LLMService
from mini.messaging.provider import MessagingProvider

logger = get_logger(__name__)


class ActionModule(AgentModule):
    def __init__(self, llm_manager: LLMService):
        self.llm_manager = llm_manager
        self.llm_manager.cost_tracking_callback = self._update_user_message_cost
        self.messaging_provider = None

    def set_messaging_provider(self, messaging_provider: MessagingProvider) -> None:
        self.messaging_provider = messaging_provider

    def generate_message(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str],
        response_format: Optional[BaseModel] = None,
    ) -> str:
        return self.llm_manager.generate_response(
            messages, system_prompt, json_mode=True, response_format=response_format
        )

    def send_message(
        self,
        text: Optional[str] = None,
        images: Optional[List[str]] = None,
        files: Optional[List[Tuple[str, str]]] = None,
        subject: Optional[str] = None,
    ) -> bool:
        """
        Send a message using the BirdMessaging. If only text is provided, it's split and sent in parts.
        For messages with images or files, everything is sent at once.

        Args:
            text (Optional[str]): The text message to send, potentially containing multiple parts separated by '|'.
            images (Optional[List[str]]): List of image URLs to send.
            files (Optional[List[Tuple[str, str]]]): List of (file_url, content_type) tuples to send.
            subject (Optional[str]): Optional subject for the message.

        Returns:
            bool: Overall success status.
        """
        if (images is None or len(images) == 0) and (files is None or len(files) == 0):
            # Text-only message: split and send in parts
            return self._send_text_message(text)
        else:
            # Message with images or files: send everything at once
            return self._send_media_message(text, images, files, subject)

    def _send_text_message(self, text: str) -> bool:
        if not text:
            logger.warning("Attempted to send empty text message")
            return False

        texts = text.split("|")
        overall_success = True

        for i, part in enumerate(texts):
            try:
                success, details = self.messaging_provider.send_message(
                    text=part.strip()
                )
                overall_success = overall_success and success
                logger.info(f"BIRD SMS SENT (Part {i+1}/{len(texts)}): {success}")
                logger.debug(f"Message details: {details}")

                # if i < len(texts) - 1:
                #     await asyncio.sleep(random.uniform(0, 10))
            except Exception as e:
                logger.error(f"Error sending text message part {i+1}: {str(e)}")
                overall_success = False

        return overall_success

    def _send_media_message(
        self,
        text: Optional[str],
        images: Optional[List[str]],
        files: Optional[List[Tuple[str, str]]],
        subject: Optional[str],
    ) -> bool:
        try:
            success, details = self.messaging_provider.send_message(
                text=text, images=images, files=files, subject=subject
            )

            logger.info(f"BIRD SMS SENT: {success}")
            logger.debug(f"Message details: {details}")
            return success
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return False

    # @chris why is this not working?
    def _update_user_message_cost(self, cost: float) -> None:
        update_data = {
            Tables.USERS__litellm_cost.value: self.user.litellm_cost + cost,
        }
        self.database_manager.update(
            table_name=Tables.USERS,
            update_data=update_data,
            condition_key=Tables.USERS__id,
            condition_value=self.user.id,
        )
