from fastapi import Header, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from config.config import config

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != config.ZOOTOPIA_API_KEY:
        raise HTTPException(
            status_code=403, 
            detail="Could not validate credentials"
        )