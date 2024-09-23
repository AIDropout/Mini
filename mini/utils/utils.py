import asyncio
import base64
import re
import subprocess
from datetime import datetime, timezone
from typing import Tuple
from zoneinfo import ZoneInfo
import uuid

import requests
from pyngrok import ngrok

from config.config import config
from mini.core.logger import get_logger
from mini.utils.storage import S3FileStore

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



def encode_image_url_to_base64(image_url: str) -> str:
    """Download image from URL and encode to base64."""
    response = requests.get(image_url)
    if response.status_code == 200:
        return base64.b64encode(response.content).decode("utf-8")
    else:
        raise Exception(f"Failed to download image from URL: {image_url}")


def upload_file(path: str, content: str, content_type: str) -> Tuple[str, str]:
    """Upload file content to S3 and return the URL and content type."""
    fs = S3FileStore()
    fs.write(path, content.encode("utf-8"), content_type)
    return fs.generate_presigned_url(path, content_type)


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def get_infostring() -> str:
    """ex: 🕒 7:40PM PT, 9/18"""
    pst_time = datetime.now(ZoneInfo("America/Los_Angeles"))
    hour = pst_time.strftime("%I").lstrip("0")
    timestamp = f"{hour}:{pst_time.strftime('%M%p')} PT, {pst_time.strftime('%-m/%-d')}"
    return f"🕒 {timestamp}"


def generate_uuid():
    return str(uuid.uuid4())
