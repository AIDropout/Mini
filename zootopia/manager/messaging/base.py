from abc import ABC, abstractmethod
from typing import Optional

from fastapi import Request

from zootopia.core.schema import ZootopiaMessage


class MessagingBase(ABC):
    @abstractmethod
    async def receive_message(cls, request: Request) -> ZootopiaMessage:
        """Handle an incoming message from a sender."""
        pass

    @abstractmethod
    async def send_message(self, message: str) -> Optional[str]:
        """Send a message to a recipient."""
        pass

    @abstractmethod
    async def register_webhook(self, webhook_url: str) -> bool:
        """Register a webhook URL for receiving updates."""
        pass
