from fastapi import APIRouter, Request, Response, HTTPException
from config.config import config
import httpx
import json
from mini.core.logger import get_logger
from mini.messaging.instagram.models import InstagramWebhook, MessageEvent

router = APIRouter()
logger = get_logger(__name__)


class InstagramWebhookService:
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

    @staticmethod
    async def handle_message_event(event: MessageEvent):
        sender_id = event.sender.id
        message_text = event.message.text

        logger.info(f"Received message from {sender_id}: {message_text}")
        response_text = f"You said: {message_text}"
        await send_message(sender_id, response_text)


async def send_message(recipient_id: str, message_text: str):
    API_VERSION = config.INSTAGRAM_CONFIG.api_version
    ACCESS_TOKEN = "IGQWRNTWJ3YjhPOFNHeTh6cUZAVLXBtSjdReVl1R0d0a1dPczJjRWVqVl9KVVAtdlNtNXhwWE9sVnY1ak5XT3ZAYSXJ3RHhnTUo0b2FGUGxCU1NUQVIydGlwTm92RG9lZAW5xN3dsUWZA3RXptUVRTZAjNzVjlDLWZAna1kZD"
    url = f"https://graph.instagram.com/{API_VERSION}/me/messages?access_token={ACCESS_TOKEN}"

    payload = {"recipient": {"id": recipient_id}, "message": {"text": message_text}}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)

    logger.info(response.json())
    response.raise_for_status()
    response_data = response.json()
    logger.info(f"Message sent successfully: {response_data}")
