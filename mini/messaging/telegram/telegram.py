"""Messaging class utilizing Telegram Bot"""

import io
import json
from typing import Optional, Union, cast

import aiohttp
import telegram

from config.config import config
from mini.core.logger import get_logger
from mini.messaging.models import (
    MessagingProviderEnum,
    MessageType,
    TelegramMetadata,
    MiniMessage,
)
from mini.messaging.telegram.models import (
    TelegramMessage,
    _TelegramMessageDocument,
    _TelegramMessagePhoto,
)

logger = get_logger(__name__)


class TelegramManager:
    def __init__(self):
        """Initialize the Telegram Bot messaging service."""
        self._bot = telegram.Bot(token=config.TELEGRAM_BOT_TOKEN)
        self._user_id = None

    def set_sender(self):
        pass

    def set_receiver(self):
        pass

    @classmethod
    def receive_message(cls, request_body) -> MiniMessage:
        """Handle an incoming message from a Telegram sender."""
        if isinstance(request_body, str):
            request_body = json.loads(request_body.replace('"from"', '"from_'))
        elif isinstance(request_body, dict):
            if "from" in request_body:
                request_body["from_"] = request_body.pop("from")
        else:
            raise ValueError("Unsupported request_body type")

        telegram_message = TelegramMessage(**request_body)

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

        return MiniMessage(
            content=telegram_message,
            metadata=metadata,
            provider=MessagingProviderEnum.TELEGRAM,
            type=message_type,
        )

    async def download_file_from_message(
        self,
        message: Union[_TelegramMessagePhoto, _TelegramMessageDocument],
    ) -> Optional[str]:
        """
        Download a file (photo or document) from a Telegram message.
        """
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

    async def send_message(self, message: str) -> Optional[str]:
        """Send a message to a Telegram recipient."""
        sent_message = await self._bot.send_message(chat_id=self._user_id, text=message)
        return str(sent_message.message_id)

    async def register_webhook(self, webhook_url: str) -> bool:
        """Register a webhook URL for receiving updates from the Telegram Bot API."""
        webhook_info = cast(telegram.WebhookInfo, await self._bot.get_webhook_info())
        if webhook_info.url == webhook_url:
            return True

        await self._bot.set_webhook(url=webhook_url)
        return True
