from fastapi import Header, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from config.config import config

security = HTTPBearer()


def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verifies the incoming request Authorization header."""
    token = credentials.credentials
    if token != config.ZOOTOPIA_API_KEY:
        raise HTTPException(status_code=403, detail="Could not validate credentials")
    return token
