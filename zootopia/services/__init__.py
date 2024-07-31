from typing import Union
from .llm.llm import LLM
from .platform.sms.bird import BirdSMSProvider
from .platform.telegram.telegram import Telegram

MessageProvider = Union[BirdSMSProvider, Telegram]


__all__ = ["LLM", "BirdSMSProvider", "Telegram", "MessageProvider"]
