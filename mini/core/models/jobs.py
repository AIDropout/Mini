from enum import Enum


class JobStatus(Enum):
    SCHEDULED = "Scheduled"
    IN_PROGRESS = "In Progress"
    COMPLETE = "Complete"
    ERROR = "Error"
    CANCELLED = "Cancelled"
