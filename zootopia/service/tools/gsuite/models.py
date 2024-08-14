from typing import List

from pydantic import BaseModel


class GAuthConfig(BaseModel):
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    # GOOGLE_AUTH_SCOPE: List[str]


class GCalError(Exception):
    """Custom exception class for Google Calendar API errors."""

    def __init__(self, message: str) -> None:
        """
        Initializes the GCalError with a specific error message.

        Args:
            message (str): The error message to be associated with the exception.
        """
        super().__init__(message)
