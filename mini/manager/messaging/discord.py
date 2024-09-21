# from mini.core.logger import get_logger
# import requests

# logger = get_logger(__name__)

# class DiscordManager:
#     def __init__(self):
#         self.deeznuts = None

#     @staticmethod
#     def send_message_to_channel(message: str, channel: str) -> bool:
#         """Send a message to a webhook url"""
#         try:
#             response = requests.post(
#                 channel,
#                 json={"content": message},
#             )
#             logger.info(f"Discord response: {response.status_code}")
#             return response.ok
#         except requests.RequestException as e:
#             logger.error(f"Failed to notify Discord: {e}")
#             return False

# discord_manager = DiscordManager()

from config.config import config
from datetime import datetime
from typing import Optional, Union
from mini.core.logger import get_logger
import requests
import traceback
from pydantic import BaseModel, HttpUrl
from zoneinfo import ZoneInfo
from mini.utils.utils import get_infostring

logger = get_logger(__name__)

class DiscordManager:
    @staticmethod
    def send_message(message: str, webhook_url: str) -> bool:
        try:
            response = requests.post(str(webhook_url), json={"content": message})
            logger.info(f"Discord response for {webhook_url}: {response.status_code}")
            return response.ok
        except requests.RequestException as e:
            logger.error(f"Failed to send message to {webhook_url}: {str(e)}")
            return False

    @classmethod
    def log_website_activity(cls, message: str) -> bool:
        formatted_message = f"{message} {cls._get_infostring()}"
        return cls.send_message(
            formatted_message, config.DISCORD_CONFIG.website_webhook_url
        )
    
    @classmethod
    def log_message(cls, message: str) -> bool:
        return cls.send_message(
            message, config.DISCORD_CONFIG.message_webhook_url
        )

    @classmethod
    def log_error(
        cls,
        error_message: str,
    ) -> bool:
        formatted_message = cls._format_error_message(error_message)
        return cls.send_message(
            formatted_message, config.DISCORD_CONFIG.error_webhook_url
        )

    @classmethod
    def _format_error_message(cls, error_message) -> str:
        environment = config.ENVIRONMENT.upper()
        error_traceback = traceback.format_exc()
        msg = f"⚠️__**{environment} ERROR**__⚠️\n-# {get_infostring()} 🏷️ {error_message}\n```{error_traceback}```"
        return msg

discord_manager = DiscordManager()
