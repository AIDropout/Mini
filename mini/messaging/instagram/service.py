from fastapi import APIRouter, Request, Response, HTTPException
from config.config import config
import httpx
import json
from mini.core.logger import get_logger
from mini.messaging.instagram.models import InstagramWebhook, MessageEvent
from mini.database.database import DatabaseManager
from mini.database.models import Tables

router = APIRouter()
logger = get_logger(__name__)


class InstagramWebhookService:
    def __init__(self, database_manager: DatabaseManager):
        self.database_manager = database_manager

    @staticmethod
    async def handle_webhook(webhook: InstagramWebhook):
        for entry in webhook.entry:
            for event in entry.messaging:
                if isinstance(event, MessageEvent):
                    await InstagramWebhookService.handle_message_event(event)
                # Add handlers for other event types as needed
                # elif isinstance(event, StoryMentionEvent):
                #     await InstagramWebhookHandler.handle_story_mention_event(event)

        return {"status": "ok"}

    async def handle_message_event(self, event: MessageEvent):
        sender_id = event.sender.id
        recipient_id = event.recipient.id
        message_text = event.message.text

        agent_ig_account = self.database_manager.get_row(
            Tables.IGACCOUNTS,
            {Tables.IGACCOUNTS__account_id: recipient_id},
        )

        logger.info(f"Received message from {sender_id}: {message_text}")
        response_text = f"You said: {message_text}"
        await send_message(sender_id, response_text)


async def send_message(recipient_id: str, message_text: str):
    API_VERSION = config.INSTAGRAM_CONFIG.api_version
    url = f"https://graph.instagram.com/{API_VERSION}/me/messages?access_token={ACCESS_TOKEN}"

    payload = {"recipient": {"id": recipient_id}, "message": {"text": message_text}}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)

    logger.info(response.json())
    response.raise_for_status()
    response_data = response.json()
    logger.info(f"Message sent successfully: {response_data}")
