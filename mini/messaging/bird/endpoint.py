from fastapi import APIRouter, Depends, Request, BackgroundTasks
from typing import Annotated

from config.container import container
from mini.core.logger import get_logger
from mini.messaging.service import ReplyService

router = APIRouter()
logger = get_logger(__name__)

ReplyServiceDep = Annotated[
    ReplyService, Depends(lambda: container.get_reply_service())
]


@router.post("/rooms/respond")
async def respond_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    reply_service: ReplyServiceDep,
):
    """Endpoint hit by incoming user messages."""
    request_body = await request.json()
    reply_service.handle_respond(request_body, background_tasks)
