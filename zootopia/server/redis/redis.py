from redis import ConnectionPool, Redis
from contextlib import contextmanager
from typing import Generator, Any, Optional
from zootopia.core.logger import get_logger
from config.config import config

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
                yield key.decode('utf-8')
