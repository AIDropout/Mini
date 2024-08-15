from .bird import BirdManager
from .telegram import TelegramManager
from .base import MessagingBase
from .messaging import MessagingManager
from typing import Union

# MessagingManager = Union[BirdManager, TelegramManager]

__all__ = ["BirdManager", "TelegramManager", "MessagingBase", "MessagingManager"]
