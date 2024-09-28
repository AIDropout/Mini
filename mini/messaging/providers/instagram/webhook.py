from fastapi import APIRouter
import json
from mini.core.logger import get_logger
from mini.messaging.providers.instagram.models import InstagramWebhook, MessageEvent
from mini.messaging.send_message.send_message import send_message
from mini.core.enums import MessageTaskType
from mini.messaging.service import MessagingService
from mini.core.models.message import MessagingProviderType
from mini.database.database import DatabaseManager
from mini.database.models import Tables

router = APIRouter()
logger = get_logger(__name__)


class InstagramWebhookService:
    def __init__(self, database_manager: DatabaseManager, factory: MessagingService):
        self.database_manager = database_manager
        self.factory = factory

    def handle_webhook(
        self,
        webhook: InstagramWebhook,
    ):
        logger.info(webhook)
        for entry in webhook.entry:
            for event in entry.messaging:
                if event.message:
                    if event.message.is_echo:
                        return  # Don't process echo
                    room_id = self.factory.process_and_store_incoming_message(
                        MessagingProviderType.INSTAGRAM, event.model_dump()
                    )
                    send_message.delay(
                        MessagingProviderType.INSTAGRAM.value,
                        room_id,
                        MessageTaskType.RESPONSE.value,
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
