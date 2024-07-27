# """Cancels the 1st message request if it's ongoing and a 2nd request comes in"""

import uuid
from typing import Optional
import redis.asyncio as redis
from zootopia.core.logger import logger
from config.config import ConcurrencyManagerConfig
from zootopia.core.exceptions import RequestCanceledException

class ConcurrencyManager:
    def __init__(self, redis_url: str, room_id: int):
        self.redis: redis.Redis = redis.from_url(redis_url)
        self.room_id: int = room_id
        self.request_id: Optional[str] = None

    @classmethod
    def from_config(cls, config: ConcurrencyManagerConfig, room_id: int) -> "ConcurrencyManager":
        return cls(redis_url=config.REDIS_URL, room_id=room_id)

    async def start_new(self) -> str:
        self.request_id = str(uuid.uuid4())
        await self.redis.set(f"room:{self.room_id}:request_id", self.request_id)
        logger.info(f"Started new request {self.request_id} for room {self.room_id}")
        return self.request_id

    async def verify_is_latest_request(self) -> bool:
        latest_request_id = await self.redis.get(f"room:{self.room_id}:request_id")

        latest_request_id = latest_request_id.decode()
        logger.info(f"Verifying request {self.request_id} for room {self.room_id}. "
                    f"Latest request: {latest_request_id}")

        if self.request_id != latest_request_id:
            raise RequestCanceledException(request_id=self.request_id, room_id=self.room_id)
        return True