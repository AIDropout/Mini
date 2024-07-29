"""Messaging class utilizing Telegram Bot"""

import io
import json
import os
from typing import Optional, Union, cast

import aiohttp
import telegram
from pydantic import ValidationError
from config.config import TelegramConfig
from zootopia.platform.platform import MessageProviderBase
from zootopia.core.schema import (
    ZootopiaMessage,
    MessageProvider,
    MessageType,
    TelegramMessage,
    _TelegramMessageDocument,
    _TelegramMessagePhoto,
    TelegramMetadata,
)
from zootopia.core.exceptions import MessageParsingError, SendMessageError, WebhookError
from zootopia.core.logger import logger


class Telegram(MessageProviderBase):
    def __init__(self, token: str):
        """Initialize the Telegram Bot messaging service."""
        self._bot = telegram.Bot(token=token)
        self._user_id = None

    @classmethod
    def from_config(cls, config: TelegramConfig) -> "Telegram":
        """Instantiate and return a Telegram object."""
        token = config.TELEGRAM_BOT_TOKEN
        return cls(token)

    @classmethod
    def receive_message(cls, request_body) -> ZootopiaMessage:
        """Handle an incoming message from a Telegram sender."""
        try:
            # Parse request body
            if isinstance(request_body, str):
                request_body = json.loads(request_body.replace('"from"', '"from_'))
            elif isinstance(request_body, dict):
                # If it's already a dict, just replace the 'from' key
                if "from" in request_body:
                    request_body["from_"] = request_body.pop("from")
            else:
                raise ValueError("Unsupported request_body type")

            telegram_message = TelegramMessage(**request_body)
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"Error parsing Telegram message data: {e}")
            raise MessageParsingError("Invalid Telegram message format.") from e

        try:
            message_type = MessageType.TEXT
            if isinstance(
                telegram_message.message,
                (_TelegramMessagePhoto, _TelegramMessageDocument),
            ):
                message_type = MessageType.FILE

            user_name = (
                f"{telegram_message.message.from_.first_name} "
                f"{telegram_message.message.from_.last_name}"
            ).strip()

            metadata = TelegramMetadata(
                uid=telegram_message.message.from_.id,
                user_name=user_name,
                chat_id=telegram_message.message.chat.id,
            )

            cls._user_id = telegram_message.message.from_.id

            return ZootopiaMessage(
                content=telegram_message,
                metadata=metadata,
                provider=MessageProvider.TELEGRAM,
                type=message_type,
            )
        except AttributeError as e:
            print(f"Error extracting data from Telegram message: {e}")
            raise MessageParsingError(
                f"Missing attribute in Telegram message: {e}"
            ) from e

    async def download_file_from_message(
        self,
        message: Union[_TelegramMessagePhoto, _TelegramMessageDocument],
    ) -> Optional[str]:
        """
        Download a file (photo or document) from a Telegram message.
        """
        try:
            if isinstance(message, _TelegramMessagePhoto):
                if not message.photo:
                    return None
                file_obj = message.photo[0]
            elif isinstance(message, _TelegramMessageDocument):
                file_obj = message.document
            else:
                return None

            # Get file information
            file = await self._bot.get_file(file_obj.file_id)
            file_path = file.file_path

            # Download the file content
            file_url = file_path
            async with aiohttp.ClientSession() as session:
                async with session.get(file_url) as response:
                    if response.status == 200:
                        content = await response.read()
                        return io.BytesIO(content)
            return None
        except Exception as e:
            logger.error(f"Error downloading the file: {e}")
            return None

    async def send_message(self, message: str) -> Optional[str]:
        """Send a message to a Telegram recipient."""
        try:
            sent_message = await self._bot.send_message(
                chat_id=self._user_id, text=message
            )
            return str(sent_message.message_id)
        except Exception as e:
            raise SendMessageError(f"Error sending message: {e}") from e

    async def register_webhook(self, webhook_url: str) -> bool:
        """Register a webhook URL for receiving updates from the Telegram Bot API."""
        webhook_info = cast(telegram.WebhookInfo, await self._bot.get_webhook_info())
        if webhook_info.url == webhook_url:
            return True

        try:
            await self._bot.set_webhook(url=webhook_url)
            return True
        except Exception as e:
            raise WebhookError(f"Error registering webhook: {e}") from e
