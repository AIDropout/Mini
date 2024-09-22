"""SMS Messaging class utilizing Bird API"""

import requests

from config.config import config
from mini.core.logger import get_logger, logger
from mini.messaging.instagram.models import MessageEvent
from mini.messaging.models import (
    MessagingProviderEnum,
    MiniMessage,
    InstagramMetadata,
    MessageType,
)
from mini.database.database import DatabaseManager
from mini.database.models import Tables
from mini.messaging.base import MessagingProvider

logger = get_logger(__name__)


class InstagramMessagingService(MessagingProvider):
    def __init__(self, database_manager: DatabaseManager):
        """Initialize Bird credentials."""
        self._api_version = config.INSTAGRAM_CONFIG.api_version
        self._access_token = None  # Page access token of the agent's account
        self._sender_id = None
        self._recipient_id = None
        self.database_manager = database_manager

    def set_receiver(self, recipient_id: str) -> None:
        """Sets id of recipient (user)"""
        self._recipient_id = recipient_id

    def set_sender(self, sender_id: str) -> None:
        """Sets id of sender"""
        self._sender_id = sender_id

    def receive_message(self, event: MessageEvent) -> MiniMessage:
        """Turn a request body into a MiniMessage"""
        recipient_id = event.recipient.id
        sender_id = event.sender.id
        message_text = event.message.text if event.message.text else "-"
        logger.info(f"Received message from {sender_id}: {message_text}")

        # Switch sender & receiver since agent is sending the message now
        self.set_sender(recipient_id)
        self.set_receiver(sender_id)

        # Fetch access token of character's account from db
        agent_ig_account = self.database_manager.get_row(
            Tables.IGACCOUNTS,
            {Tables.IGACCOUNTS__account_id: recipient_id},
        )
        if not agent_ig_account:
            logger.error(f"No Instagram account found for recipient_id: {recipient_id}")
            return

        self._access_token = agent_ig_account.access_token

        # Construct the Mini Message
        return MiniMessage(
            content=message_text,
            metadata=InstagramMetadata(sender_id, recipient_id),
            provider=MessagingProviderEnum.BIRD,
            type=MessageType.TEXT,  # TODO: Handle files
            media_urls=None,
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
