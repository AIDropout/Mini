import traceback
from functools import wraps
from zootopia.core.logger import logger
from zootopia.core.exceptions import MessageParsingError, ServiceError
from pydantic import ValidationError

def error_handler(service_name):
    """Decorator to handle API errors consistently"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ValidationError as e:
                error_details = traceback.format_exc()
                logger.error(
                    f"Validation error in {service_name} operation {func.__name__}:\n{error_details}"
                )
                raise MessageParsingError(
                    f"Invalid data in {service_name}: {e.errors()}"
                )
            except (KeyError, ValueError) as e:
                error_details = traceback.format_exc()
                logger.error(
                    f"Parsing error in {service_name} operation {func.__name__}:\n{error_details}"
                )
                raise MessageParsingError(
                    f"Invalid message format in {service_name}: {str(e)}"
                )
            except Exception as e:
                error_details = traceback.format_exc()
                logger.error(
                    f"Error in {service_name} operation {func.__name__}:\n{error_details}"
                )
                raise ServiceError(
                    f"Unexpected error in {service_name} operation: {str(e)}"
                )

        return wrapper

    return decorator