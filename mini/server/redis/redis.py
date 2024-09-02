from contextlib import contextmanager
from time import time
from typing import Any, Generator, Optional

from redis import ConnectionPool, Redis

from config.config import config
from mini.core.logger import get_logger

logger = get_logger(__name__)


class RedisManager:
    def __init__(self):
        self.pool = None

    def initialize(self) -> None:
        if self.pool is None:
            self.pool = ConnectionPool.from_url(config.REDIS_URL)
            logger.info("Redis pool initialized")

    @contextmanager
    def get_connection(self) -> Generator[Redis, None, None]:
        if self.pool is None:
            self.initialize()
        client = Redis(connection_pool=self.pool)
        try:
            yield client
        finally:
            client.close()

    def close(self):
        if self.pool:
            self.pool.disconnect()
            self.pool = None
            logger.info("Redis connection pool closed")

    def set(self, key: str, value: Any, expiry: Optional[int] = None) -> None:
        """Set a key-value pair in Redis, with an optional expiry time in seconds."""
        with self.get_connection() as client:
            if expiry is not None:
                client.setex(key, expiry, value)
            else:
                client.set(key, value)

    def get(self, key: str) -> Any:
        """Get the value for a given key from Redis."""
        with self.get_connection() as client:
            return client.get(key)

    def delete(self, key: str) -> None:
        """Delete a key from Redis."""
        with self.get_connection() as client:
            client.delete(key)

    def scan_iter(self, match: str, count: int = 100) -> Generator[str, None, None]:
        """Scan Redis for keys matching a pattern."""
        with self.get_connection() as client:
            for key in client.scan_iter(match=match, count=count):
                yield key.decode("utf-8")

    def check_rate_limit(self, key: str, max_calls: int, period: int) -> bool:
        """
        Check if the rate limit has been exceeded for a given key.

        :param key: The rate limit key (e.g., phone number and IP combination)
        :param max_calls: Maximum number of calls allowed in the period
        :param period: Time period in seconds
        :return: True if rate limited, False otherwise
        """
        with self.get_connection() as client:
            current_time = int(time())
            rate_limit_key = f"rate_limit:{key}"

            pipe = client.pipeline()
            pipe.zremrangebyscore(rate_limit_key, 0, current_time - period)
            pipe.zcard(rate_limit_key)
            pipe.zadd(rate_limit_key, {str(current_time): current_time})
            pipe.expire(rate_limit_key, period)
            _, call_count, _, _ = pipe.execute()

            return call_count >= max_calls
