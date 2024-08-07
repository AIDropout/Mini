from datetime import datetime
from typing import Optional, Dict, Any
from zootopia.core.logger import logger as core_logger

class EventLogger:
    def __init__(self):
        self.event_log: Dict[str, Any] = {"entries": []}

    def log(self, step: str, details: str, exception: Optional[Exception] = None):
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "step": step,
            "details": details
        }
        
        if exception:
            log_entry["exception"] = str(exception)

        self.event_log["entries"].append(log_entry)

        log_message = f"[{step}] {details}"
        if exception:
            log_message += f" - Exception: {str(exception)}"

        core_logger.info(log_message)

    def get_event_log(self) -> Dict[str, Any]:
        return self.event_log

event_logger = EventLogger()