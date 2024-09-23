from typing import Dict
from typing import Union

from mini.core.models.message import MessagingProviderEnum
from mini.messaging.bird.bird import BirdMessaging
from mini.messaging.instagram.instagram import InstagramMessaging

MessagingProvider = Union[BirdMessaging, InstagramMessaging]

messaging_providers: Dict[MessagingProviderEnum, MessagingProvider] = {
    MessagingProviderEnum.BIRD: BirdMessaging(),
    MessagingProviderEnum.INSTAGRAM: InstagramMessaging(),
}


__all__ = ["messaging_providers, MessagingProvider"]
