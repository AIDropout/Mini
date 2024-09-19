from typing import Union

from .bird.bird import BirdManager
from .factory import MessagingManagerFactory
from .telegram import TelegramManager
from .discord import discord_manager

MessagingManager = Union[BirdManager]

__all__ = [
    "BirdManager",
    "TelegramManager",
    "MessagingManagerFactory",
    "MessagingManager",
    "discord_manager",
]
