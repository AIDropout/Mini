import redis
from redis import Redis
from config.config import config

redis_url: str = config.REDIS_URL
redis_client: Redis = redis.from_url(redis_url)


def get_redis_client() -> Redis:
    return redis_client
