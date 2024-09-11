import json
import re

from litellm.exceptions import RateLimitError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from mini.core.exceptions import MessageParsingError
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


def parse_content(content: str, response_format: dict | None = None):
    """Parse the content based on the response format."""
    if response_format and response_format.get("type", "") == "json_object":

        start_index = content.find("{")
        end_index = content.rfind("}") + 1
        cleaned_output = content[start_index:end_index].strip()
        cleaned_output = re.sub(r"\n|\r", "", cleaned_output)
        cleaned_output = re.sub(r"\s+", " ", cleaned_output)

        try:
            return json.loads(cleaned_output)
        except json.JSONDecodeError as e:
            raise MessageParsingError(f"Invalid JSON output: {content}") from e
    return content
