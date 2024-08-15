"""Initialized by main:app"""

from redis import ConnectionPool, Redis
from zootopia.core.logger import get_logger
from config.config import config

logger = get_logger(__name__)


class RedisManager:
    def __init__(self):
        self.pool = None

    def initialize(self) -> None:
        self.pool = ConnectionPool.from_url(config.REDIS_URL)
        if not self.pool:
            raise RuntimeError("Redis pool not initialized")
        logger.info("Redis pool initialized")

    def get_client(self) -> Redis:
        if not self.pool:
            self.initialize()
        return Redis(connection_pool=self.pool)

    def close(self):
        if self.pool:
            self.pool.disconnect()
            logger.info("Redis connection pool closed")

    def get_scheduled_task(self, room_id: str) -> str:
        """Get the scheduled task ID for a given room."""
        return self.get_client().get(f"scheduled_task:{room_id}")

    def delete_scheduled_task(self, room_id: str) -> None:
        """Delete the scheduled task for a given room."""
        self.get_client().delete(f"scheduled_task:{room_id}")

    def set_scheduled_task(self, room_id: str, task_id: str, expiry: int) -> None:
        """Set a scheduled task for a given room with an expiry time."""
        client = self.get_client()
        client.set(f"scheduled_task:{room_id}", task_id)
        client.expire(f"scheduled_task:{room_id}", expiry)


redis_manager = RedisManager()
