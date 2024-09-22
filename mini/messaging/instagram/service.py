from fastapi import APIRouter
from config.config import config
import requests
from mini.core.logger import get_logger
from mini.messaging.instagram.models import InstagramWebhook, MessageEvent
from mini.database.database import DatabaseManager
from mini.database.models import Tables

router = APIRouter()
logger = get_logger(__name__)


class InstagramWebhookService:
    def __init__(self, database_manager: DatabaseManager):
        self.database_manager = database_manager

    def handle_webhook(self, webhook: InstagramWebhook):
        logger.info(webhook)
        for entry in webhook.entry:
            for event in entry.messaging:
                if event.message:
                    self._handle_message_event(event)
                elif event.read:
                    self._handle_read_receipt(event)
                else:
                    logger.warning(f"Received unknown event type: {event}")
        return {"status": "ok"}

    def _handle_message_event(self, event: MessageEvent):
        if event.message.is_echo:
            return  # Don't process echoes
        logger.info("🟢 User sent us a message")

        sender_id = event.sender.id
        recipient_id = event.recipient.id
        message_text = event.message.text if event.message.text else "No text content"

        logger.info(f"Received message from {sender_id}: {message_text}")

        agent_ig_account = self.database_manager.get_row(
            Tables.IGACCOUNTS,
            {Tables.IGACCOUNTS__account_id: recipient_id},
        )

        if not agent_ig_account:
            logger.error(f"No Instagram account found for recipient_id: {recipient_id}")
            return

        response_text = f"You said: {message_text}"
        try:
            self._send_message(sender_id, response_text, agent_ig_account.access_token)
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")

    def _handle_read_receipt(self, event: MessageEvent):
        logger.info("🟢 User read our message")

        sender_id = event.sender.id
        recipient_id = event.recipient.id
        read_mid = event.read.mid
        
        logger.info(f"Received read receipt from {sender_id} for message: {read_mid}")
        

    def _send_message(self, recipient_id: str, message_text: str, access_token: str):
        API_VERSION = config.INSTAGRAM_CONFIG.api_version
        url = f"https://graph.instagram.com/{API_VERSION}/me/messages?access_token={access_token}"

        payload = {"recipient": {"id": recipient_id}, "message": {"text": message_text}}

        response = requests.post(url, json=payload)
        logger.info(response.json())
        response.raise_for_status()
