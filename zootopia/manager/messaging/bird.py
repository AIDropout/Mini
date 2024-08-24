"""SMS Messaging class utilizing Bird API"""

from typing import Any, Dict, Optional, Tuple, List
import requests
from config.config import config
from zootopia.core.logger import logger
from zootopia.manager.messaging.base import MessagingBase
from zootopia.core.schema.message import (
    ZootopiaMessage,
    MessageProvider,
    MessageType,
    BirdMetadata,
)
from zootopia.core.schema.bird import BirdRequest
from zootopia.core.schema.sms_otp import VerificationStatus, ErrorCode
from zootopia.core.error import error_handler
import asyncio
from zootopia.core.logger import get_logger
import os
from urllib.parse import urlparse
from pathlib import Path
from zootopia.storage import get_file_store
from uuid import uuid4

logger = get_logger(__name__)


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

    def set_receiver(self, user_phone: str) -> None:
        """Sets phone number of receiver"""
        self._user_phone = user_phone

    def set_sender(self, channel_id: str) -> None:
        """Sets phone number of sender"""
        self._channel_id = channel_id

    @error_handler("Bird SMS")
    def receive_message(self, request_body: dict) -> ZootopiaMessage:
        """Handle an incoming message from a Bird SMS sender."""
        request_object = BirdRequest.model_validate(request_body)

        bird_message = request_object.payload
        phone_number = bird_message.sender.contact.identifierValue
        channel_id = bird_message.channelId
        self.set_receiver(phone_number)
        self.set_sender(channel_id)

        body = bird_message.body
        message_type = MessageType.TEXT
        content = ""
        aws_media_urls = []

        if body.type == "text" and body.text:
            message_type = MessageType.TEXT
            content = body.text.text
        elif body.type == "file" and body.file:
            if body.file.text:
                message_type = MessageType.TEXT_AND_FILE
                content = body.file.text
            else:
                message_type = MessageType.FILE

            bird_media_urls = [file.mediaUrl for file in body.file.files]

            # Upload media to AWS and get URLs
            fs = get_file_store()
            for api_url in bird_media_urls:
                try:
                    response = requests.get(api_url, headers=self._api_header)
                    response.raise_for_status()
                    key = f"{config.ENVIRONMENT}/{uuid4()}"
                    fs.write(key, response.content)
                    url = fs.generate_presigned_url(key)
                    aws_media_urls.append(url)
                except requests.RequestException as e:
                    logger.error(f"Failed to download media from {api_url}: {e}")

        text_part = f"text [{content}]" if content else "no text"
        image_part = f"{len(aws_media_urls)} media files"
        logger.info(f"Received message with {text_part} and {image_part}")

        return ZootopiaMessage(
            content=content,
            metadata=BirdMetadata(channel_id=channel_id, phone_number=phone_number),
            provider=MessageProvider.BIRD,
            type=message_type,
            media_urls=aws_media_urls,
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
        response_data = response.json()
        response.raise_for_status()  # This will raise an HTTPError for bad responses

        details = {
            "channel_id": self._channel_id,
            "phone_number": self._user_phone,
            "message_length": len(message),
            "status_code": response.status_code,
            "response_data": response_data,
        }

        logger.info(response_data)  # Why can't i see this

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
        timeout: int = 120,
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
            verification_data["steps"][0]["attempts"][0]["status"] == "accepted"
            if verification_data["steps"]
            else False
        )
        expires_at = verification_data.get("expiresAt", "")
        verification_id = verification_data.get("id", "")

        return is_sent, expires_at, verification_id

    @error_handler("Bird SMS")
    async def resend_verification(
        self, verification_id: str
    ) -> Tuple[bool, bool, Optional[str]]:
        """
        Resend a verification code for a given verification ID.

        Args:
            verification_id (str): The ID of the verification to resend.

        Returns:
            Tuple[bool, bool, Optional[str]]: A tuple containing:
                - bool: Whether the resend request was accepted
                - bool: Whether the verification process is still active
                - Optional[str]: The expiration time of the new verification code, or None if not applicable
        """
        url = f"{self._api_url}/workspaces/{self._workspace_id}/verify/{verification_id}/resend"

        payload = {}
        try:
            response = requests.post(url, headers=self._api_header, json=payload)
            response_data = response.json()
            logger.info(
                f"Resend verification response for ID {verification_id}: {response_data}"
            )

            if response.status_code == 202:  # Accepted
                is_sent = True
                expires_at = response_data.get("expiresAt")
                status = response_data.get("status")
                is_active = status in [
                    VerificationStatus.ACCEPTED.value,
                    VerificationStatus.PENDING.value,
                ]
                return is_sent, is_active, expires_at
            else:
                response.raise_for_status()  # This will raise an HTTPError for non-2xx status codes

        except requests.exceptions.HTTPError as e:
            error_data = e.response.json()
            error_code = error_data.get("code")
            error_message = error_data.get("message", "Unknown error")

            if error_code == ErrorCode.MAX_ATTEMPTS_REACHED:
                logger.warning(
                    f"Max attempts reached for verification ID {verification_id}: {error_message}"
                )
                return False, False, None  # Not sent, not active, no expiration
            else:
                logger.error(
                    f"HTTP error in resend verification for ID {verification_id}: {error_message}"
                )
                return (
                    False,
                    True,
                    None,
                )  # Not sent, but might still be active, no expiration

        except Exception as e:
            logger.error(
                f"Unexpected error during resend verification for ID {verification_id}: {str(e)}"
            )
            return False, False, None  # Not sent, not active, no expiration

        # This line should never be reached, but added for completeness
        return False, False, None

    @error_handler("Bird SMS")
    async def verify_code(self, verification_id: str, code: str) -> Tuple[bool, bool]:
        """
        Verify a code for a given verification ID.

        Args:
            verification_id (str): The ID of the verification to check.
            code (str): The verification code to verify.

        Returns:
            VerifyCodeResponse: Contains whether the code was successfully verified,
                                if the verification process is still active,
                                and the current status of the verification.
        """
        url = (
            f"{self._api_url}/workspaces/{self._workspace_id}/verify/{verification_id}"
        )
        payload = {"code": code}

        try:
            response = requests.post(url, headers=self._api_header, json=payload)
            response.raise_for_status()
            verification_data = response.json()

            logger.info(
                f"Verification response for ID {verification_id}: {verification_data}"
            )

            status = verification_data.get("status")

            print(status)
            print(VerificationStatus.VERIFIED.value)

            is_verified = status == VerificationStatus.VERIFIED.value
            is_active = status in [
                VerificationStatus.ACCEPTED.value,
                VerificationStatus.PENDING.value,
            ]
            print(is_verified)
            print(is_active)
            print("______")

            return is_verified, is_active

        except requests.exceptions.HTTPError as e:
            error_data = e.response.json()
            error_code = error_data.get("code")
            error_message = error_data.get("message", "Unknown error")

            if error_code == ErrorCode.MAX_ATTEMPTS_REACHED.value:
                logger.warning(f"Maxed attempts reached for ID {verification_id}. ")
                return False, False
            elif error_code == ErrorCode.VERIFICATION_CODE_MISMATCH.value:
                details = error_data.get("details", {})
                logger.warning(
                    f"Incorrect code for ID {verification_id}. "
                    f"Failed attempts: {details.get('failedAttempts')}, "
                    f"Remaining attempts: {details.get('remainingAttempts')}"
                )
                return False, True  # Not verified, but still active
            else:
                logger.error(
                    f"Verification failed for ID {verification_id}: {error_message}"
                )

            return False, True  # Not verified, but still active

        except Exception as e:
            logger.error(
                f"Unexpected error during verification for ID {verification_id}: {str(e)}"
            )
            return False, False  # Not verified and not active due to unexpected error


async def main():
    bird_sms = BirdManager()
    bird_sms.set_receiver("+13142952259")
    bird_sms.set_sender("4e127266-e6de-4081-a6f6-702015f48e6d")
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
