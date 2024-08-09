from typing import List, Dict, Any
from datetime import datetime
from zootopia.core.logger import logger as core_logger

class EventLogger:
    def __init__(self):
        self.logs: List[Dict[str, Any]] = []

    def log(self, message: str):
        log_entry = {
            "log": message,
            "timestamp": datetime.now().isoformat()
        }
        self.logs.append(log_entry)
        core_logger.info(message)

    def get_logs(self) -> List[Dict[str, Any]]:
        return self.logs

event_logger = EventLogger()