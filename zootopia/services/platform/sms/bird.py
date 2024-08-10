"""SMS Messaging class utilizing Bird API"""

from typing import Any, Dict, Optional, Tuple
import requests
from functools import wraps
from zootopia.core.config import config
from zootopia.core.logger import logger
from ..platform import MessageProviderBase
from zootopia.core.schema import (
    ZootopiaMessage,
    MessageProvider,
    MessageType,
    BirdMetadata,
)
from pydantic import ValidationError
from zootopia.core.error import error_handler


class BirdSMSProvider(MessageProviderBase):
    def __init__(self):
        """Initialize Bird credentials."""
        self._api_url = config.BIRD_API_URL
        self._api_header = {
            "Authorization": f"AccessKey {config.BIRD_API_KEY}",
            "Content-Type": "application/json",
        }
        self._signing_key = config.BIRD_SIGNING_KEY
        self._organization_id = config.BIRD_ORGANIZATION_ID
        self._workspace_id = config.BIRD_WORKSPACE_ID
        self._user_phone = None
        self._channel_id = None

    def set_user_phone(self, user_phone: str) -> None:
        self._user_phone = user_phone

    def set_channel_id(self, channel_id: str) -> None:
        self._channel_id = channel_id

    @error_handler("Bird SMS")
    def receive_message(self, request_body: dict) -> ZootopiaMessage:
        """Handle an incoming message from a Bird SMS sender."""
        bird_message = request_body["payload"]
        phone_number = bird_message["sender"]["contact"]["identifierValue"]
        channel_id = bird_message["channelId"]
        self.set_user_phone(phone_number)
        self._channel_id = channel_id
        message_text = bird_message["body"]["text"]["text"]

        metadata = BirdMetadata(channel_id=channel_id, phone_number=phone_number)
        message_type = MessageType.TEXT

        return ZootopiaMessage(
            content=message_text,
            metadata=metadata,
            provider=MessageProvider.BIRD,
            type=message_type,
        )

    @error_handler("Bird SMS")
    async def send_message(self, message: str) -> Tuple[bool, Dict[str, Any]]:
        """Send a Bird SMS message to the recipient."""
        url = f"{self._api_url}/workspaces/{self._workspace_id}/channels/{self._channel_id}/messages"
        payload = {
            "receiver": {"contacts": [{"identifierValue": self._user_phone}]},
            "body": {"type": "text", "text": {"text": message}},
        }
        response = requests.post(url, headers=self._api_header, json=payload)
        response.raise_for_status()  # This will raise an HTTPError for bad responses
        response_data = response.json()

        details = {
            "channel_id": self._channel_id,
            "phone_number": self._user_phone,
            "message_length": len(message),
            "status_code": response.status_code,
            "response_data": response_data,
        }

        if response.status_code == 202 and response_data.get("status") == "accepted":
            return True, details
        else:
            return False, details

    @error_handler("Bird SMS")
    async def register_webhook(
        self, event: str = "sms.inbound", webhook_url: str = None
    ) -> None:
        """Register a webhook URL for receiving text events from Bird API."""
        url = f"{self._api_url}/organizations/{self._organization_id}/workspaces/{self._workspace_id}/webhook-subscriptions"
        body = {
            "service": "channels",
            "event": event,
            "url": webhook_url,
            "signingKey": self._signing_key,
            "eventFilters": [{"key": "channelId", "value": self._channel_id}],
        }

        webhooks = self._get_existing_webhooks()
        for webhook in webhooks["results"]:
            if ".ngrok-free.app" in webhook["url"]:
                self._delete_webhook(webhook["id"])

        response = requests.post(url, headers=self._api_header, json=body)
        response.raise_for_status()
        logger.info(f"Webhook registration response: {response.json()}")

    @error_handler("Bird SMS")
    def _get_existing_webhooks(self) -> Dict:
        """Retrieves the list of subscribed webhooks."""
        url = f"{self._api_url}/organizations/{self._organization_id}/workspaces/{self._workspace_id}/webhook-subscriptions"
        response = requests.get(url, headers=self._api_header)
        response.raise_for_status()
        return response.json()

    @error_handler("Bird SMS")
    def _delete_webhook(self, webhook_id: str) -> None:
        """Deletes a Bird webhook given a webhook id."""
        url = f"{self._api_url}/organizations/{self._organization_id}/workspaces/{self._workspace_id}/webhook-subscriptions/{webhook_id}"
        response = requests.delete(url, headers=self._api_header)
        response.raise_for_status()
