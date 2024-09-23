"""SMS Messaging class utilizing Bird API"""

from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import requests

from config.config import config
from mini.core.logger import get_logger, logger
from mini.messaging.bird.models import BirdRequest
from mini.core.models.message import (
    MessagingProviderEnum,
    MessageType,
    MiniMessage,
    MiniMessageMetadata,
)
from mini.messaging.base import ProviderBase
from mini.messaging.bird.models import ErrorCode, VerificationStatus
from mini.utils.storage import get_file_store

logger = get_logger(__name__)


class BirdMessaging(ProviderBase):
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

    def receive_message(self, request_body: dict) -> MiniMessage:
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
        logger.info(f"💬 Received message with {text_part} and {image_part}")

        return MiniMessage(
            content=content,
            metadata=MiniMessageMetadata(
                sender_id=channel_id, receiver_id=phone_number
            ),
            provider=MessagingProviderEnum.BIRD,
            type=message_type,
            media_urls=aws_media_urls,
        )

    def send_message(
        self,
        text: Optional[str] = None,
        images: Optional[List[str]] = None,
        files: Optional[List[Tuple[str, str]]] = None,
        subject: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Send a Bird SMS message to the recipient, with optional text, images, files, and subject.

        :param text: Optional text message
        :param images: Optional list of image URLs
        :param files: Optional list of tuples (file_url, content_type)
        :param subject: Optional subject for the message
        :return: Tuple of success status and details
        """
        url = f"{self._api_url}/workspaces/{self._workspace_id}/channels/{self._channel_id}/messages"

        if images and files:
            raise ValueError("Cannot send both images and files in the same message")

        if images:
            payload = self._create_image_payload(text, images, subject)
        elif files:
            payload = self._create_file_payload(text, files, subject)
        elif text:
            payload = self._create_text_payload(text)
        else:
            raise ValueError(
                "At least one of message, images, or files must be provided"
            )

        return self._send_request(url, payload)

    def _create_text_payload(self, text: str) -> Dict:
        return {
            "receiver": {"contacts": [{"identifierValue": self._user_phone}]},
            "body": {"type": "text", "text": {"text": text}},
        }

    def _create_image_payload(
        self, text: Optional[str], images: List[str], subject: Optional[str]
    ) -> Dict:
        payload = {
            "receiver": {"contacts": [{"identifierValue": self._user_phone}]},
            "body": {
                "type": "image",
                "image": {
                    "images": [{"mediaUrl": url} for url in images],
                },
            },
        }
        if text:
            payload["body"]["image"]["text"] = text
        if subject:
            payload["body"]["image"]["metadata"] = {"subject": subject}
        return payload

    def _create_file_payload(
        self,
        text: Optional[str],
        files: List[Tuple[str, str]],
        subject: Optional[str],
    ) -> Dict:
        payload = {
            "receiver": {"contacts": [{"identifierValue": self._user_phone}]},
            "body": {
                "type": "file",
                "file": {
                    "files": [
                        {"mediaUrl": url, "contentType": content_type}
                        for url, content_type in files
                    ],
                },
            },
        }
        if text:
            payload["body"]["file"]["text"] = text
        if subject:
            payload["body"]["file"]["metadata"] = {"subject": subject}
        return payload

    def _send_request(self, url: str, payload: Dict) -> Tuple[bool, Dict[str, Any]]:
        """Send a request to Bird API and handle the response."""
        try:
            response = requests.post(url, headers=self._api_header, json=payload)
            response_data = response.json()
            logger.info(f"Bird API response: {response_data}")
            response.raise_for_status()

            details = {
                "channel_id": self._channel_id,
                "phone_number": self._user_phone,
                "message_type": payload["body"]["type"],
                "status_code": response.status_code,
                "response_data": response_data,
            }

            if (
                response.status_code == 202
                and response_data.get("status") == "accepted"
            ):
                return True, details
            else:
                return False, details
        except requests.RequestException as e:
            logger.error(f"Error sending message: {str(e)}")
            return False, {"error": str(e)}

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
        logger.info(response.json())
        response.raise_for_status()

    def _get_existing_webhooks(self) -> Dict:
        """Retrieves the complete list of subscribed webhooks."""
        url = f"{self._api_url}/organizations/{self._organization_id}/workspaces/{self._workspace_id}/webhook-subscriptions"
        all_webhooks = []
        page_token = None

        while True:
            params = {"pageToken": page_token} if page_token else {}
            response = requests.get(url, headers=self._api_header, params=params)
            response.raise_for_status()
            data = response.json()

            all_webhooks.extend(data.get("results", []))

            page_token = data.get("nextPageToken")
            if not page_token:
                break

        return {"results": all_webhooks}

    def _delete_webhook(self, webhook_id: str) -> None:
        """Deletes a Bird webhook given a webhook id."""
        url = f"{self._api_url}/organizations/{self._organization_id}/workspaces/{self._workspace_id}/webhook-subscriptions/{webhook_id}"
        response = requests.delete(url, headers=self._api_header)
        response.raise_for_status()

    def send_verification(
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

    def resend_verification(
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

    def verify_code(self, verification_id: str, code: str) -> Tuple[bool, bool]:
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

            if (
                error_message
                == "Unexpected Verification Status: verification already verified"
            ):
                logger.info(error_message)
                logger.warning(f"Unexpected verification status {verification_id}. ")
                return True, False
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
