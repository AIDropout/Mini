# logger.py
import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(name="zootopia", celery_logging=False):
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        return logger  # Prevent adding handlers if they already exist

    logger.setLevel(logging.INFO)

    # Create formatters
    verbose_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    simple_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)

    # File Handler
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
    )
    file_handler.setFormatter(verbose_formatter)
    logger.addHandler(file_handler)

    if celery_logging:
        # Setup Celery logging
        from celery.signals import after_setup_logger

        @after_setup_logger.connect
        def setup_celery_logging(logger, *args, **kwargs):
            logger.addHandler(console_handler)
            logger.addHandler(file_handler)

    return logger


# Create and export the logger
logger = setup_logger(celery_logging=True)
