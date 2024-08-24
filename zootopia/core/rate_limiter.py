from zootopia.server.redis.redis import redis_manager

class RateLimiter:
    def __init__(self, max_calls: int, period: int):
        self.max_calls = max_calls
        self.period = period

    def is_allowed(self, key: str) -> bool:
        return not redis_manager.check_rate_limit(key, self.max_calls, self.period)