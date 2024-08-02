from pydantic import BaseModel, Field


class IntentTypeSchema(BaseModel):
    FILTER: str = Field(default="filter")
    """Filters a user or agent message before further processing.
    """

    SCHEDULE: str = Field(default="schedule")
    """Searches long-term memory
    """

    SKIP: str = Field(default="skip")
    """Doesn't respond to a use
    """


IntentType = IntentTypeSchema()
