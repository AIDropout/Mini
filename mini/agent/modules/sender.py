from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel

from config.config import config
from mini.agent.modules.base import AgentModule
from mini.core.event_logger import event_logger as el
from mini.core.logger import get_logger
from mini.core.models.context import Context
from mini.database.database import DatabaseManager
from mini.database.models import Message, Tables
from mini.llm import LLMService
from mini.messaging.providers import MessagingProvider
from mini.messaging.providers.discord import discord_manager
from mini.utils.time import TimeManager
from mini.utils.utils import utc_now

logger = get_logger(__name__)


class MessageSenderModule(AgentModule):
    def __init__(
        self,
        database_manager: DatabaseManager,
        system_time_manager: TimeManager,
        context: Context,
        llm_manager: LLMService,
    ):
        super().__init__(database_manager, context)
        self.llm_manager = llm_manager
        self.llm_manager.cost_tracking_callback = self._update_user_message_cost
        self.messaging_provider = None
        self.system_time_manager = system_time_manager

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
            bool: Sent message.
        """
        success: bool
        if (images is None or len(images) == 0) and (files is None or len(files) == 0):
            success = self._send_text_message(text)
        else:
            success = self._send_media_message(text, images, files, subject)

        # Store & log message
        if success:
            el.log(f"BIRD SMS SENT: {success}")
            self._handle_successful_send(text)

        return success

    def _send_text_message(self, text: str) -> bool:
        # Text-only message: split and send in parts

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
        # Message with images or files: send everything at once
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

    # TODO: @chris why is this not working?
    def _update_user_message_cost(self, cost: float) -> None:
        update_data = {
            Tables.USERS__litellm_cost.value: self.context.user.litellm_cost + cost,
        }
        self.database_manager.update(
            table_name=Tables.USERS,
            update_data=update_data,
            condition_key=Tables.USERS__id,
            condition_value=self.context.user.id,
        )

    def _handle_successful_send(self, final_message: str):
        self._add_message_to_db(final_message)
        self._log_to_discord(final_message)
        self._update_room_last_message_time()

    def _add_message_to_db(self, final_message: str):
        self.database_manager.insert(
            Tables.MESSAGES,
            Message(
                room_id=self.context.room.id,
                sender_id=self.context.agent.id,
                content=final_message,
                log=el.get_logs(),
            ),
        )

    def _log_to_discord(self, final_message: str):
        if config.ENVIRONMENT == "production":
            discord_manager.log_message(
                message=f"-# {self.context.agent.name} -> {self.context.user.phone_number}: {final_message}",
            )

    def _update_room_last_message_time(self):
        time_stamp = self.system_time_manager.get_user_timestamp()
        self.database_manager.update(
            Tables.ROOMS,
            {Tables.ROOMS__agent_last_msg_sent_at: time_stamp},
            condition_key=Tables.ROOMS__id,
            condition_value=self.context.room.id,
        )
