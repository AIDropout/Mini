from enum import Enum


class ConfidenceLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

    def __ge__(self, other: "ConfidenceLevel") -> bool:
        levels = ["LOW", "MEDIUM", "HIGH"]
        return levels.index(self) >= levels.index(other)
