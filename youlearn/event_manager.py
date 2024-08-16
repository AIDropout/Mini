from typing import Dict, List, Awaitable, Optional, Callable
import asyncio
from pydantic import BaseModel
from fastapi import Request
from models.events import EventType
from patterns.singleton import SingletonMeta
from utils.logger import get_logger
from utils.request import extract_request_info
from models.events import EventType

logger = get_logger(__name__)


class EventManager(metaclass=SingletonMeta):
    POST_EVENTS = True

    def __init__(
        self,
    ) -> None:
        self.subscribers: Dict[str,
                               List[Callable[[Dict], Awaitable[None]]]] = {}

    def subscribe(self, event_types: List[EventType], fn: Callable[[Dict], Awaitable[None]]) -> None:
        """Create an event for observers to subscribe to.

        Args:
            event_type (str): The event you want to log
            fn (Callable): an async function that notifes the observers. The function should contain one Dict parameter.
        """
        for event in event_types:
            event_key = event.name
            if not event_key in self.subscribers:
                self.subscribers[event_key] = []
                self.subscribers[event_key].append(fn)
            else:
                self.subscribers[event_key].append(fn)

    async def post_event(self, event_type: EventType, data: Optional[Dict | BaseModel] = None, request: Optional[Request] = None):
        if not self.POST_EVENTS:
            logger.info(f"POST_EVENTS is False. Skipped notifying subscribers")
            return

        if isinstance(data, BaseModel):
            data = data.model_dump()
        event_data = {
            **data,
            'request_info': extract_request_info(request) if request else {},
            'event': event_type.name.lower()
        }

        event_key = event_type.name
        if not event_key in self.subscribers:
            return

        try:
            logger.debug(f"Posting event {event_key} to subscribers")
            await asyncio.gather(*(fn(event_data) for fn in self.subscribers[event_key]), return_exceptions=False)
        except Exception as e:
            logger.exception(e)


def register_events(event_types: List[EventType]):
    """function decorator to subscribe to a particular event.
    The function should be awaitable, have one Dict parameter.

    Args:
        event_type (List[EventType]): a list of events you want to subscribe to.
    """
    def decorator(func):
        EventManager().subscribe(event_types, func)

        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator
