from typing import Annotated

from fastapi import APIRouter, Path, Depends

from config.container import container
from mini.core.logger import get_logger
from mini.core.security import ApiKeyDep
from mini.database.database import DatabaseManager
from mini.server.redis import RedisManager
from mini.messaging.models import MessagingProviderEnum
from mini.messaging.context import ContextFactory
from mini.server.schedule.service import ProactiveService
from mini.server.cancel import CancelManager


router = APIRouter()
logger = get_logger(__name__)


@router.post("/rooms/proactive/{room_id}")
def send_proactive_message(
    api_key: ApiKeyDep,
    room_id: Annotated[str, Path(..., title="Room ID for proactive messaging")],
    database_manager: Annotated[DatabaseManager, Depends(DatabaseManager)],
    redis_manager: Annotated[RedisManager, Depends(RedisManager)],
    context_factory: Annotated[ContextFactory, Depends(container.get_context_factory)],
    cancel_manager: Annotated[CancelManager, Depends(container.get_cancel_manager)],
):
    """Endpoint for sending proactive messages."""
    service = ProactiveService(
        database_manager, redis_manager, context_factory, cancel_manager
    )
    service.send_proactive_message(room_id, provider=MessagingProviderEnum.BIRD)
