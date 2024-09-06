from typing import Union

from .bird import BirdManager
from .factory import MessagingManagerFactory
from .telegram import TelegramManager

MessagingManager = Union[BirdManager]

__all__ = [
    "BirdManager",
    "TelegramManager",
    "MessagingManagerFactory",
    "MessagingManager",
]
