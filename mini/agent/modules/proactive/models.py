from datetime import datetime

from pydantic_settings import BaseSettings


class ScheduledMessageTemplate(BaseSettings):
    reason_for_message: str
    scheduled_time: datetime
