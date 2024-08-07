from enum import Enum
from fastapi import HTTPException
from pydantic import BaseModel


class RoomAlreadyExistsError(Exception):
    def __init__(self, phone_number: str, agent_id: int):
        super().__init__(
            f"Room with agent '{agent_id} & '{phone_number}' already exists"
        )


class LLMResponseParsingError(Exception):
    def __init__(self, message="Failed to parse LLM response"):
        super().__init__(message)


class AgentNotFoundError(Exception):
    def __init__(self, message):
        super().__init__(message)


class DatabaseConnectionError(Exception):
    def __init__(self, message="Failed to connect to the database"):
        super().__init__(message)


class SMSServiceError(Exception):
    def __init__(self, message="Failed to send SMS"):
        super().__init__(message)


class RoomCreationError(Exception):
    def __init__(self, message="Failed to create or get room"):
        super().__init__(message)


class MessageParsingError(Exception):
    """Custom exception for errors during message parsing."""


class SendMessageError(Exception):
    """Custom exception for errors during sending messages."""


class WebhookError(Exception):
    """Custom exception for errors during webhook registration."""


class MessageInsertError(Exception):
    def __init__(self, room_id: int, original_error: Exception, message: str = None):
        self.room_id = room_id
        self.original_error = original_error
        default_message = f"Failed to insert message into database for room_id {room_id}: {str(original_error)}"
        super().__init__(message or default_message)

    def __str__(self):
        return f"MessageInsertError: {self.args[0]} (Room ID: {self.room_id}, Original error: {self.original_error})"


class RequestCanceledException(Exception):
    def __init__(self, room_id: int):
        super().__init__(
            f"🟠 Previous request in room '{room_id}' canceled due to this task"
        )
