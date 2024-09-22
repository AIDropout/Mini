from fastapi import Depends
from typing import Annotated

from config.container import container
from mini.messaging.service import MessagingService

MessagingServiceDep = Annotated[
    MessagingService, Depends(lambda: container.get_messaging_service())
]
