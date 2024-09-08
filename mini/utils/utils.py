from datetime import datetime
from zoneinfo import ZoneInfo
import re
import asyncio
import subprocess
from pyngrok import ngrok

from config.config import config
from mini.core.logger import get_logger
from mini.manager.messaging import BirdManager, TelegramManager
import traceback
from mini.core.logger import get_logger
from mini.manager.messaging import discord_manager


logger = get_logger(__name__)


def is_ngrok_url(url: str) -> bool:
    ngrok_pattern = r"^https?://[a-zA-Z0-9-]+\.ngrok-free\.app"
    return bool(re.match(ngrok_pattern, url))


def stop_existing_processes(port: int) -> None:
    """Stops all local server processes for main.py"""

    try:
        pids = subprocess.check_output(["lsof", "-t", f"-i:{port}"]).split()
        for pid in pids:
            logger.info(f"Killing process {pid.decode()} using port {port}")
            subprocess.run(["kill", "-9", pid.decode()])
        logger.info("Stopped all server processes")
    except subprocess.CalledProcessError:
        logger.info(f"No processes found using port {port}")


async def configure_local_webhooks(local_url: str) -> None:
    """Sets up an Ngrok public URL, and directs received Bird/Telegram messages to the URL"""

    ngrok_connection = ngrok.connect(addr=local_url, proto="http")
    logger.info(f"Ngrok public URL: {ngrok_connection.public_url}")

    webhook = f"{ngrok_connection.public_url}/rooms/respond"
    _telegram = TelegramManager()
    _bird = BirdManager()

    _bird.set_sender(config.BIRD_DEV_CHANNEL_ID)

    await asyncio.gather(
        _telegram.register_webhook(webhook),
        _bird.register_webhook(event="sms.inbound", webhook_url=webhook),
    )

    logger.info("Ngrok and webhooks successfully set up!")


def get_infostring() -> str:
    environment = config.ENVIRONMENT

    pst_time = datetime.now(ZoneInfo("America/Los_Angeles"))
    hour = pst_time.strftime("%I").lstrip("0")
    timestamp = f"{hour}:{pst_time.strftime('%M%p')} PT, {pst_time.strftime('%-m/%-d')}"

    return f"ENV={environment.upper()} 🕒 {timestamp}"


def log_error_to_discord(identifier_key: str, identifier_value) -> str:
    error_traceback = traceback.format_exc()
    msg = f"⚠️__**ERROR**__⚠️\n-# {get_infostring()} 🏷️ {identifier_key}={identifier_value}\n```{error_traceback}```"
    discord_manager.send_message_to_channel(
        msg, config.DISCORD_CONFIG.server_status_webhook_url
    )
    return msg
