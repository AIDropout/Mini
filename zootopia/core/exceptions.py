from enum import Enum
from fastapi import HTTPException
from pydantic import BaseModel

class RoomAlreadyExistsError(Exception):
    def __init__(self, phone_number: str, agent_id: int):
        super().__init__(f"Room with agent '{agent_id} & '{phone_number}' already exists")


class AgentNotFoundError(Exception):
    def __init__(self, agent_id=None):
        if agent_id is not None:
            message = f"No agent found with id '{agent_id}'"
        else:
            message = 'Agent not found'
        super().__init__(message)


class DatabaseConnectionError(Exception):
    def __init__(self, message='Failed to connect to the database'):
        super().__init__(message)


class SMSServiceError(Exception):
    def __init__(self, message='Failed to send SMS'):
        super().__init__(message)


class RoomCreationError(Exception):
    def __init__(self, message='Failed to create or get room'):
        super().__init__(message)


class MessageCreationError(Exception):
    def __init__(self, message='Failed to create message'):
        super().__init__(message)

class MessageParsingError(Exception):
    """Custom exception for errors during message parsing."""


class SendMessageError(Exception):
    """Custom exception for errors during sending messages."""


class WebhookError(Exception):
    """Custom exception for errors during webhook registration."""
