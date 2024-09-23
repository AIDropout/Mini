from typing import Annotated

from fastapi import Depends

from config.container import container
from mini.server.schedule.service import ProactiveService

ProactiveServiceDep = Annotated[
    ProactiveService, Depends(lambda: container.get_proactive_service())
]
