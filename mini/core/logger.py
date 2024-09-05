import logging
import os
from typing import Optional


def get_logger(name: Optional[str] = None, log_level: int = logging.INFO) -> logging.Logger:
    """
    Get a logger with a specified name and log level.

    Args:
        name (str, optional): Name of the logger. If None, returns the root logger.
        log_level (int, optional): The log level. Defaults to logging.INFO.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    # logger.propagate = False
    logger.setLevel(log_level)


    # Avoid adding handlers if they already exist
    if not logger.handlers:
        # Create log directory
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(log_dir, exist_ok=True)

        # Create formatters and handlers
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        
        file_handler = logging.FileHandler(os.path.join(log_dir, "app.log"))
        file_handler.setFormatter(formatter)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

# Usage
logger = get_logger(__name__)