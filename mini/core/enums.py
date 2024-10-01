from enum import Enum


class ConfidenceLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

    def __ge__(self, other: "ConfidenceLevel") -> bool:
        levels = ["LOW", "MEDIUM", "HIGH"]
        return levels.index(self) >= levels.index(other)


class MessageTaskType(Enum):
    RESPONSE = "Response"
    PROACTIVE = "Proactive"
    REMIND = "Remind"


class JobStatus(Enum):
    SCHEDULED = "Scheduled"
    IN_PROGRESS = "In Progress"
    COMPLETE = "Complete"
    ERROR = "Error"
    CANCELLED = "Cancelled"

class MessagingProviderType(Enum):
    BIRD = "Bird"
    INSTAGRAM = "Instagram"
    TELEGRAM = "Telegram"
