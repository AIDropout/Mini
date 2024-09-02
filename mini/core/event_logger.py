from datetime import datetime
from typing import Any, Dict, List

from mini.core.logger import logger as core_logger


class EventLogger:
    """Collects logs that get stored in the database at the end of a request (for observability)"""

    def __init__(self):
        self.logs: List[Dict[str, Any]] = []

    def log(self, message: str):
        cleaned_message = self._clean_string(message)
        log_entry = {"log": cleaned_message, "timestamp": datetime.now().isoformat()}
        self.logs.append(log_entry)
        core_logger.info(cleaned_message)

    def get_logs(self) -> List[Dict[str, Any]]:
        return self.logs

    @staticmethod
    def _clean_string(s: str) -> str:
        """Remove newlines and extra whitespace from a string."""
        return " ".join(s.split())


event_logger = EventLogger()
