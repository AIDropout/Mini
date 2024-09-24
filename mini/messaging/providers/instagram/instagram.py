"""SMS Messaging class utilizing Bird API"""

import requests

from config.config import config
from mini.core.logger import get_logger, logger
from mini.messaging.providers.instagram.models import MessageEvent
from mini.core.models.message import (
    MessagingProviderEnum,
    MiniMessage,
    MiniMessageMetadata,
    MessageType,
)
from mini.database.database import DatabaseManager
from mini.database.models import Tables
from mini.messaging.providers.base import ProviderBase

logger = get_logger(__name__)


class InstagramMessaging(ProviderBase):
    def __init__(self):
        """Initialize Bird credentials."""
        self._api_version = config.INSTAGRAM_CONFIG.api_version
        self._access_token = None  # Page access token of the agent's account
        self._sender_id = None
        self._recipient_id = None

    def set_receiver(self, recipient_id: str) -> None:
        """Sets id of recipient (user)"""
        self._recipient_id = recipient_id

    def set_sender(self, sender_id: str) -> None:
        """Sets id of sender"""
        self._sender_id = sender_id

    def receive_message(self, request_body: dict) -> MiniMessage:
        event = MessageEvent.model_validate_json(request_body)
        """Turn a request body into a MiniMessage"""
        recipient_id = event.recipient.id  # Agent
        sender_id = event.sender.id  # User
        message_text = event.message.text if event.message.text else "-"
        logger.info(f"Received message from {sender_id}: {message_text}")

        # Switch sender & receiver since agent is sending the message now
        self.set_sender(recipient_id)
        self.set_receiver(sender_id)

        # Construct the Mini Message
        return MiniMessage(
            content=message_text,
            metadata=MiniMessageMetadata(
                sender_id=self._sender_id, receiver_id=self._recipient_id
            ),
            provider=MessagingProviderEnum.INSTAGRAM,
            type=MessageType.TEXT,  # TODO: Handle files
            media_urls=[],
        )

    def send_message(self, text: str):
        url = f"https://graph.instagram.com/{self._api_version}/me/messages?access_token={self._access_token}"

        payload = {
            "recipient": {"id": self._recipient_id},
            "message": {"text": text},
        }

        response = requests.post(url, json=payload)
        logger.info(response.json())
        response.raise_for_status()
