from abc import ABC, abstractmethod
from typing import Optional

from fastapi import Request

from mini.core.schema.message import MiniMessage


class MessagingBase(ABC):
    @abstractmethod
    async def receive_message(cls, request: Request) -> MiniMessage:
        """Handle an incoming message from a sender."""
        pass

    @abstractmethod
    async def set_receiver(self) -> Optional[str]:
        """Set the user identifier."""
        pass

    @abstractmethod
    async def set_sender(self) -> Optional[str]:
        """Set the agent identifier."""
        pass

    @abstractmethod
    async def send_message(self, message: str) -> Optional[str]:
        """Send a message to a recipient."""
        pass

    @abstractmethod
    async def register_webhook(self, webhook_url: str) -> bool:
        """Register a webhook URL for receiving updates."""
        pass
