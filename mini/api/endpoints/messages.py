from typing import List, Annotated
from fastapi import APIRouter, Depends, Path, Body

from config.container import container
from mini.api.security import ApiKeyDep
from mini.core.logger import get_logger
from mini.database.models import Agent
from mini.messaging.providers.bird import BirdMessaging
from mini.database.models import Agent, Message, Room, Tables


router = APIRouter(
    tags=["messages"],
)
logger = get_logger(__name__)


@router.post("/messages", response_model=Agent)
def send_message(
    room_id: Annotated[str, Body(..., title="The room ID to send a message to")],
    content: Annotated[str, Body(..., title="The message content")],
    api_key: ApiKeyDep,
) -> Message:
    logger.info(room_id, content)
    context = container.message_task_factory._get_context_from_room_id(room_id)
    messaging_provider = BirdMessaging()


    messaging_provider.set_receiver(context.user.phone_number)
    messaging_provider.set_sender(context.agent.bird_channel_id)

    messaging_provider.send_message(text=content)

    # Start a session
    new_session = container.session_table_service.get_or_start_active_session(room_id)

    # Log the initial message
    return container.database_manager.insert(
        table_name=Tables.MESSAGES,
        item=Message(
            room_id=room_id,
            sender_id=context.agent.id,
            content=content,
            session_id=new_session.id,
        ),
    )
