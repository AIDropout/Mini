from config.config import config
from mini.core.logger import get_logger
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

logger = get_logger(__name__)

class DiscordManager:
    def __init__(self):
        self.deeznuts = None

    @staticmethod
    def send_message_to_channel(message: str, channel: str) -> bool:
        environment = config.ENVIRONMENT
        
        pst_time = datetime.now(ZoneInfo("America/Los_Angeles"))
        hour = pst_time.strftime("%I").lstrip('0')
        timestamp = f"{hour}:{pst_time.strftime('%M%p')} PT, {pst_time.strftime('%-m/%-d')}"
        
        full_message = f"---------------------\n[{environment.upper()}][🕒{timestamp}]\n{message}"

        """Send a message to a webhook url"""
        try:
            response = requests.post(
                channel,
                json={"content": full_message},
            )
            logger.info(f"Discord response: {response.status_code}")
            return response.ok
        except requests.RequestException as e:
            logger.error(f"Failed to notify Discord: {e}")
            return False

discord_manager = DiscordManager()