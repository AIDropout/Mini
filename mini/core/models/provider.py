from typing import Union
from mini.messaging.bird.bird import BirdMessagingService
from mini.messaging.instagram.instagram import InstagramMessagingService

MessagingProvider = Union[BirdMessagingService, InstagramMessagingService]
