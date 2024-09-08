from fastapi import (
    APIRouter,
    Body,
    Depends,
    Path,
    Request,
    Security,
)

from config.container import container
from mini.api.security import verify_api_key
from mini.core.logger import get_logger
from mini.core.schema.tables import Room
from mini.service.dashboard_service import DashboardService
from mini.service.reply_service import ReplyService
from mini.service.room_service import RoomService

router = APIRouter()
logger = get_logger(__name__)


@router.get("/rooms/{user_id}")
def get_rooms(
    user_id: str = Path(..., title="The user's ID"),
    room_service: RoomService = Depends(lambda: container.get_room_service()),
    api_key: str = Security(verify_api_key),
) -> Room:
    """Creates a room and sends the first message to the user"""
    return room_service.get_user_rooms(user_id=user_id)


@router.post("/rooms")
def create_room(
    agent_id: str = Body(..., title="Agent ID of the page the user signed up to"),
    user_id: str = Body(..., title="The user's ID"),
    room_service: RoomService = Depends(lambda: container.get_room_service()),
    api_key: str = Security(verify_api_key),
) -> Room:
    """Creates a room and sends the first message to the user"""
    return room_service.create_room(agent_id=agent_id, user_id=user_id)


@router.post("/rooms/respond")
async def respond_webhook(
    request: Request,
    reply_service: ReplyService = Depends(lambda: container.get_reply_service()),
):
    """Endpoint hit by incoming user messages."""
    request_body = await request.json()
    reply_service.handle_respond(request_body)


@router.post("/rooms/admin-message")
def send_admin_message(
    room_id: str = Body(..., title="Room ID of the page the user signed up to"),
    message: str = Body(..., title="Message to send to user"),
    dashboard_service: DashboardService = Depends(
        lambda: container.get_dashboard_service()
    ),
    api_key: str = Security(verify_api_key),
):
    """Endpoint for sending messages from the admin dashboard."""
    dashboard_service.send_admin_message(room_id, message)
