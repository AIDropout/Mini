from mini.core.logger import get_logger
import requests

logger = get_logger(__name__)

class DiscordManager:
    def __init__(self):
        self.deeznuts = None

    @staticmethod
    def send_message_to_channel(message: str, channel: str) -> bool:
        """Send a message to a webhook url"""
        try:
            response = requests.post(
                channel,
                json={"content": message},
            )
            logger.info(f"Discord response: {response.status_code}")
            return response.ok
        except requests.RequestException as e:
            logger.error(f"Failed to notify Discord: {e}")
            return False

discord_manager = DiscordManager()