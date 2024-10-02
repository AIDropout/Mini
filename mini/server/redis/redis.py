from typing import Any, Generator, List, Tuple
from redis import ConnectionPool, Redis
import json
from time import time

from config.config import config
from mini.core.logger import get_logger

logger = get_logger(__name__)

class RedisManager:
    def __init__(self) -> None:
        self.pool = None
        self.client = None

    def initialize(self) -> None:
        if self.pool is None:
            self.pool = ConnectionPool.from_url(config.REDIS_URL)
            self.client = Redis(connection_pool=self.pool)
            logger.info("Redis pool initialized")

    def close(self):
        if self.client:
            self.client.close()
        if self.pool:
            self.pool.disconnect()
            self.pool = None
            self.client = None
            logger.info("Redis connection pool closed")

    def _ensure_connection(self):
        if self.client is None:
            self.initialize()

    def set(self, key: str, value: Any) -> None:
        """Set a key-value pair in Redis."""
        self._ensure_connection()
        self.client.set(key, value)

    def get(self, key: str) -> Any:
        """Get the value for a given key from Redis."""
        self._ensure_connection()
        return self.client.get(key)

    def delete(self, key: str) -> None:
        """Delete a key from Redis."""
        self._ensure_connection()
        self.client.delete(key)

    def scan_iter(self, match: str, count: int = 100) -> Generator[str, None, None]:
        """Scan Redis for keys matching a pattern."""
        self._ensure_connection()
        for key in self.client.scan_iter(match=match, count=count):
            yield key.decode("utf-8")

    def check_rate_limit(self, key: str, max_calls: int, period: int) -> bool:
        """
        Check if the rate limit has been exceeded for a given key.

        :param key: The rate limit key (e.g., phone number and IP combination)
        :param max_calls: Maximum number of calls allowed in the period
        :param period: Time period in seconds
        :return: True if rate limited, False otherwise
        """
        self._ensure_connection()
        current_time = int(time())
        rate_limit_key = f"rate_limit:{key}"

        pipe = self.client.pipeline()
        pipe.zremrangebyscore(rate_limit_key, 0, current_time - period)
        pipe.zcard(rate_limit_key)
        pipe.zadd(rate_limit_key, {str(current_time): current_time})
        pipe.expire(rate_limit_key, period)
        _, call_count, _, _ = pipe.execute()

        return call_count >= max_calls

    def lpush(self, key: str, value: str) -> None:
        """Push a value to the head of the list stored at key."""
        self._ensure_connection()
        self.client.lpush(key, value)

    def ltrim(self, key: str, start: int, end: int) -> None:
        """Trim a list so that it will contain only the specified range of elements."""
        self._ensure_connection()
        self.client.ltrim(key, start, end)

    def lindex(self, key: str, index: int) -> bytes:
        """Get an element from a list by its index."""
        self._ensure_connection()
        return self.client.lindex(key, index)

    def lrem(self, key: str, count: int, value: Any) -> int:
        """Remove elements from a list."""
        self._ensure_connection()
        return self.client.lrem(key, count, value)

    def get_tasks(self, room_id: str) -> List[str]:
        """
        Retrieves all tasks for a room.
        """
        self._ensure_connection()
        tasks = self.client.lrange(f"tasks:{room_id}", 0, -1)
        return [task.decode('utf-8') for task in tasks]