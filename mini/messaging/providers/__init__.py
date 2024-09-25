from typing import Dict
from typing import Union

from mini.core.models.message import MessagingProviderType
from mini.messaging.providers.bird import BirdMessaging
from mini.messaging.providers.instagram import InstagramMessaging

MessagingProvider = Union[BirdMessaging, InstagramMessaging]

messaging_providers: Dict[MessagingProviderType, MessagingProvider] = {
    MessagingProviderType.BIRD: BirdMessaging(),
    MessagingProviderType.INSTAGRAM: InstagramMessaging(),
}


__all__ = ["messaging_providers, MessagingProvider"]
