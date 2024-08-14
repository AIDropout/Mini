from .bird import BirdSMSProvider
from .telegram import Telegram
from .base import MessagingBase
from typing import Union

MessageProvider = Union[BirdSMSProvider, Telegram]

__all__ = ["BirdSMSProvider", "Telegram", "MessageProvider"]
