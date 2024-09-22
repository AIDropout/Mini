from fastapi import APIRouter, BackgroundTasks
from config.config import config
import requests
from mini.core.logger import get_logger
from mini.messaging.instagram.models import InstagramWebhook, MessageEvent
from mini.messaging.service import MessagingService
from mini.messaging.models import MessagingProviderEnum
from mini.database.database import DatabaseManager
from mini.database.models import Tables

router = APIRouter()
logger = get_logger(__name__)


class InstagramWebhookService:
    def __init__(
        self, messaging_service: MessagingService, database_manager: DatabaseManager
    ):
        self.database_manager = database_manager
        self.messaging_service = messaging_service

    def handle_webhook(
        self, webhook: InstagramWebhook, background_tasks: BackgroundTasks
    ):
        logger.info(webhook)
        for entry in webhook.entry:
            for event in entry.messaging:
                if event.message:
                    if event.message.is_echo:
                        return # Don't process echo
                    self.messaging_service.handle_incoming_message(
                        MessagingProviderEnum.INSTAGRAM, event, background_tasks
                    )
                elif event.read:
                    self._handle_read_receipt(event)
                else:
                    logger.warning(f"Received unknown event type: {event}")
        return {"status": "ok"}

    def _handle_read_receipt(self, event: MessageEvent):
        logger.info("🟢 User read our message")

        sender_id = event.sender.id
        recipient_id = event.recipient.id
        read_mid = event.read.mid

        logger.info(f"Received read receipt from {sender_id} for message: {read_mid}")
