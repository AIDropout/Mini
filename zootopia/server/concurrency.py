# """Cancels the 1st message request if it's ongoing and a 2nd request comes in"""

import uuid
from typing import Optional
from zootopia.server.redis import redis_client
from zootopia.core.logger import logger
from config.config import ConcurrencyManagerConfig
from zootopia.core.exceptions import RequestCanceledException

class ConcurrencyManager:
    def __init__(self, room_id: int):
        self.redis = redis_client
        self.room_id: int = room_id
        self.request_id: Optional[str] = None

    @classmethod
    def from_config(cls, room_id: int) -> "ConcurrencyManager":
        return cls(room_id=room_id)

    async def start_new(self) -> str:
        try:
            self.request_id = str(uuid.uuid4())
            self.redis.set(f"room:{self.room_id}:request_id", self.request_id)
            logger.info(f"Started new request {self.request_id} for room {self.room_id}")
            
            return self.request_id
        except Exception as e:
            logger.error(f"Error starting new request for room {self.room_id}: {str(e)}")
            return None

    async def verify_is_latest_request(self) -> None:
        try:
            latest_request_id = self.redis.get(f"room:{self.room_id}:request_id")
            
            if latest_request_id is None:
                logger.warning(f"No request ID found for room {self.room_id}")

            latest_request_id = latest_request_id.decode()
            logger.info(f"Verifying request {self.request_id} for room {self.room_id}. "
                        f"Latest request: {latest_request_id}")

            if self.request_id != latest_request_id:
                raise RequestCanceledException(request_id=self.request_id, room_id=self.room_id)
            
        except RequestCanceledException:
            logger.info(f"Request {self.request_id} for room {self.room_id} was canceled.")
            raise
        except Exception as e:
            logger.error(f"Error verifying request {self.request_id} for room {self.room_id}: {str(e)}")
