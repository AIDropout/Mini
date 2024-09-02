from mini.server.redis import RedisManager


class RateLimiter:
    def __init__(self, redis_manager: RedisManager, max_calls: int, period: int):
        self.redis_manager = redis_manager
        self.max_calls = max_calls
        self.period = period

    def is_allowed(self, key: str) -> bool:
        return not self.redis_manager.check_rate_limit(key, self.max_calls, self.period)
