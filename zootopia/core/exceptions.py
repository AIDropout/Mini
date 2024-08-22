from datetime import datetime
from enum import Enum

from fastapi import HTTPException
from pydantic import BaseModel


class ServiceError(Exception):
    pass


class TimeManagerError(Exception):
    """Base class for exceptions raised by TimeManager."""

    pass


class TimezoneFetchError(TimeManagerError):
    """Exception raised for errors in fetching timezones."""

    pass


class TimeFetchError(TimeManagerError):
    """Exception raised for errors in fetching time data."""

    pass


class InvalidTimezoneError(TimeManagerError):
    """Exception raised for invalid timezones."""

    pass


class RoomAlreadyExistsError(Exception):
    def __init__(self, phone_number: str, agent_id: str):
        super().__init__(
            f"Room with agent '{agent_id} & '{phone_number}' already exists"
        )


class LLMResponseParsingError(Exception):
    def __init__(self, message="Failed to parse LLM response"):
        super().__init__(message)


class DatabaseConnectionError(Exception):
    def __init__(self, message="Failed to connect to the database"):
        super().__init__(message)


class RoomCreationError(Exception):
    def __init__(self, message="Failed to create or get room"):
        super().__init__(message)


class MessageParsingError(Exception):
    """Custom exception for errors during message parsing."""


class MessageInsertError(Exception):
    def __init__(self, room_id: str, original_error: Exception, message: str = None):
        self.room_id = room_id
        self.original_error = original_error
        default_message = f"Failed to insert message into database for room_id {room_id}: {str(original_error)}"
        super().__init__(message or default_message)

    def __str__(self):
        return f"MessageInsertError: {self.args[0]} (Room ID: {self.room_id}, Original error: {self.original_error})"
