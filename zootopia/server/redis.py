from redis import ConnectionPool, Redis
from zootopia.core.logger import logger
from config.config import config


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


redis_manager = RedisManager()