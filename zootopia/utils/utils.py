import re
from typing import Dict, Any, Optional
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json
from zootopia.core.logger import logger


def is_ngrok_url(url: str) -> bool:
    ngrok_pattern = r"^https?://[a-zA-Z0-9-]+\.ngrok-free\.app"
    return bool(re.match(ngrok_pattern, url))