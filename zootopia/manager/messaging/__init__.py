from .bird import BirdManager
from .telegram import TelegramManager
from .factory import MessagingManagerFactory
from typing import Union

MessagingManager = Union[BirdManager, TelegramManager]

__all__ = [
    "BirdManager",
    "TelegramManager",
    "MessagingManagerFactory",
    "MessagingManager",
]
