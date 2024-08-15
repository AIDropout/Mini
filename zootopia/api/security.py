"""Include the 'X-API-Key' header in your request, with your API key as its value."""

from fastapi import Header, HTTPException, Security
from fastapi.security import APIKeyHeader
from config.config import config

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def verify_api_key(api_key: str = Security(api_key_header)):
    """Verifies the incoming request header"""

    if api_key != config.ZOOTOPIA_API_KEY:
        raise HTTPException(status_code=403, detail="Could not validate credentials")
