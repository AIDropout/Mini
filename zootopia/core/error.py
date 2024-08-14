import traceback
from functools import wraps
import json
from zootopia.core.logger import logger
from zootopia.core.exceptions import MessageParsingError, ServiceError, HTTPException
from pydantic import ValidationError
import requests

def error_handler(service_name):
    """Decorator to handle API errors consistently with detailed error reporting"""

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
            except requests.exceptions.HTTPError as e:
                error_details = traceback.format_exc()
                response_content = None
                if e.response is not None:
                    try:
                        response_content = e.response.json()
                    except json.JSONDecodeError:
                        response_content = e.response.text
                
                error_message = (
                    f"HTTP error in {service_name} operation {func.__name__}:\n"
                    f"Status code: {e.response.status_code}\n"
                    f"Response content: {json.dumps(response_content, indent=2) if response_content else 'N/A'}\n"
                    f"Error details:\n{error_details}"
                )
                logger.error(error_message)
                raise HTTPException(error_message)
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