from enum import Enum


class TaskType(str, Enum):
    RESPOND = "respond"
    REMIND = "remind"
    REVIVE = "revive"
    PROACTIVE = "proactive"
