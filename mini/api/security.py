from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Annotated

from config.config import config
from mini.core.logger import get_logger


logger = get_logger(__name__)
security = HTTPBearer()


def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verifies the incoming request Authorization header.

    i.e. When calling our endpoints, add "Bearer {OUR_API_KEY}" to the Authorization header
    """
    token = credentials.credentials
    if token != config.BACKEND_API_KEY:
        raise HTTPException(status_code=403, detail="Could not validate credentials")
    return token


ApiKeyDep = Annotated[str, Security(verify_api_key)]
