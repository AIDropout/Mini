from litellm.exceptions import RateLimitError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from mini.core.logger import get_logger

logger = get_logger(__name__)


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(RateLimitError),
    reraise=True,
)
def execute_with_retry(func, *args, **kwargs):
    """Execute a function with retry logic."""
    try:
        return func(*args, **kwargs)
    except RateLimitError as e:
        logger.error("Rate limit exceeded after multiple retries: %s", e)
        raise
    except Exception as e:
        logger.error("Unexpected error after multiple retries: %s", e)
        raise
