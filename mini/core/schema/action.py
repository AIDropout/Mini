"""Note: Actions are currently not implemented. None of the action files are being used."""

from dataclasses import dataclass
from typing import Dict, Union

from pydantic import BaseModel, Field

__all__ = ["ActionType", "Action", "ActionResults"]


@dataclass
class Action:
    type: str
    args: Dict[str, Union[str, int, float, bool]]


@dataclass
class ActionResult:
    action: Action
    success: bool
    result: Union[str, Dict]


class ActionTypeSchema(BaseModel):
    MESSAGE: str = Field(default="message")
    """Represents a message.
    """

    RECALL: str = Field(default="recall")
    """Searches long-term memory
    """

    WEB_SEARCH: str = Field(default="web_search")
    """Conducts a web search
    """

    NO_RESPONSE: str = Field(default="no_response")
    """Don't send a message
    """

    FLAG_USER: str = Field(default="flag_message")
    """For attempting to jailbreak, violating terms, etc.
    """

    UPLOAD_GDRIVE_FILE: str = Field(default="web_search")
    """Authorizes user and uploads given file to google drive
    """

    ADD_GCAL_EVENT: str = Field(default="web_search")
    """Adds an event to google calendar
    """

    SCHEDULE: str = Field(default="schedule")
    """To be designed
    """

    NULL: str = Field(default="null")


ActionType = ActionTypeSchema()
