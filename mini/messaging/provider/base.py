from abc import ABC, abstractmethod
from typing import Optional

from fastapi import Request

from mini.core.models.message import MiniMessage


class ProviderBase(ABC):
    @abstractmethod
    def receive_message(cls, request: Request) -> MiniMessage:
        """Handle an incoming message from a sender."""
        pass

    @abstractmethod
    def set_receiver(self) -> Optional[str]:
        """Set the user identifier."""
        pass

    @abstractmethod
    def set_sender(self) -> Optional[str]:
        """Set the agent identifier."""
        pass

    @abstractmethod
    def receive_message(self, request_body: dict) -> MiniMessage:
        """Convert a raw request body to a Mini message"""
        pass
    
    @abstractmethod
    def send_message(self, message: str) -> Optional[str]:
        """Send a message to a recipient."""
        pass
    
