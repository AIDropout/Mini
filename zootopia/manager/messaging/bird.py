"""SMS Messaging class utilizing Bird API"""

from typing import Any, Dict, Optional, Tuple
import requests
from config.config import config
from zootopia.core.logger import logger
from zootopia.manager.messaging.base import MessagingBase
from zootopia.core.schema import (
    ZootopiaMessage,
    MessageProvider,
    MessageType,
    BirdMetadata,
)
from zootopia.core.error import error_handler
import asyncio


# logger = get_logger(__name__)


class BirdManager(MessagingBase):
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
        """Sets phone number of receiver"""
        self._user_phone = user_phone

    def set_channel_id(self, channel_id: str) -> None:
        """Sets phone number of sender"""
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
        print("neart💜💜💜")
        logger.info("heart💜💜💜")

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

        logger.info(response_data) # Why can't i see this

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

    @error_handler("Bird SMS")
    async def send_verification(
        self,
        locale: str = "en-US",
        max_attempts: int = 3,
        timeout: int = 600,
        code_length: int = 6,
    ) -> Tuple[bool, str, str]:
        """
        Send a verification code to the user's phone number using the Bird API.

        Args:
            locale (str): The locale/language of the message. Defaults to "en-US".
            max_attempts (int): Maximum number of verification attempts. Defaults to 3.
            timeout (int): Time in seconds before the verification expires. Defaults to 600.
            code_length (int): Length of the verification code. Defaults to 6.

        Returns:

        Tuple[bool, str, str]: A tuple containing:
            - bool: Whether the message was sent successfully
            - str: The expiration time of the verification code
            - str: The verification ID
        """
        url = f"{self._api_url}/workspaces/{self._workspace_id}/verify"

        payload = {
            "identifier": {"phonenumber": self._user_phone},
            "locale": locale,
            "maxAttempts": max_attempts,
            "timeout": timeout,
            "codeLength": code_length,
            "steps": [{"channelId": self._channel_id}],
        }

        response = requests.post(url, headers=self._api_header, json=payload)
        print(response.json())
        response.raise_for_status()

        verification_data = response.json()

        # Log the verification request
        logger.info(f"Verification request sent: {verification_data['id']}")

        is_sent = (
            verification_data["steps"][0]["attempts"][0]["status"] == "sent"
            if verification_data["steps"]
            else False
        )
        expires_at = verification_data.get("expiresAt", "")
        verification_id = verification_data.get("id", "")

        return is_sent, expires_at, verification_id

    @error_handler("Bird SMS")
    async def verify_code(self, verification_id: str, code: str) -> Tuple[bool, str]:
        """
        Verify a code for a given verification ID.

        Args:
            verification_id (str): The ID of the verification to check.
            code (str): The verification code to verify.

        Returns:
            Tuple[bool, str]: A tuple containing:
                - bool: Whether the code was successfully verified
        """
        url = (
            f"{self._api_url}/workspaces/{self._workspace_id}/verify/{verification_id}"
        )

        payload = {"code": code}

        response = requests.post(url, headers=self._api_header, json=payload)
        response.raise_for_status()

        verification_data = response.json()
        logger.info(
            f"Verification attempt for ID {verification_id}: {verification_data['status']}"
        )

        return verification_data["status"] == "verified"

    @error_handler("Bird SMS")
    async def resend_verification(
        self, verification_id: str, step_index: int = None
    ) -> Tuple[bool, str, str]:
        """
        Resend a verification code for a given verification ID.

        Args:
            verification_id (str): The ID of the verification to resend.
            step_index (int, optional): The index of the step to use. If not provided, uses the currently active step.

        Returns:
            Tuple[bool, str, str]: A tuple containing:
                - bool: Whether the resend request was accepted
                - str: The expiration time of the new verification code
                - str: The status of the verification after resending
        """
        url = f"{self._api_url}/workspaces/{self._workspace_id}/verify/{verification_id}/resend"

        payload = {}
        if step_index is not None:
            payload["stepIndex"] = step_index

        response = requests.post(url, headers=self._api_header, json=payload)
        response.raise_for_status()

        verification_data = response.json()
        logger.info(
            f"Verification resend for ID {verification_id}: {verification_data['status']}"
        )

        is_sent = response.status_code == 202
        expires_at = verification_data.get("expiresAt", "")
        status = verification_data["status"]

        return is_sent, expires_at, status


async def main():
    bird_sms = BirdManager()
    bird_sms.set_user_phone("+13142952259")
    bird_sms.set_channel_id("4e127266-e6de-4081-a6f6-702015f48e6d")
    try:
        # Send message
        result = await bird_sms.send_message("hi")
        print(result)

        # Send verification
        # is_sent, expires_at, verification_id = await bird_sms.send_verification()
        # print(f"Verification sent: {is_sent}, Expires at: {expires_at}, ID: {verification_id}")

        # Verify code (you would get this code from the user in a real scenario)
        # is_verified, status = await bird_sms.verify_code(
        #     verification_id="c8d3a75a-a232-4ac8-bb51-1a88fc6a724d", code="876813"
        # )
        # print(f"Code verified: {is_verified}, Status: {status}")

        # # Resend verification if needed
        # is_accepted, new_expires_at, new_status = await bird_sms.resend_verification(verification_id)
        # print(f"Resend accepted: {is_accepted}, New expiration: {new_expires_at}, New status: {new_status}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
