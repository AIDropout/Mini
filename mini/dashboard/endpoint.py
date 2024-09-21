from fastapi import (
    APIRouter,
    Body,
    Depends,
)
from typing import Annotated

from config.container import container
from mini.core.security import ApiKeyDep
from mini.core.logger import get_logger
from mini.dashboard.service import DashboardService

router = APIRouter()
logger = get_logger(__name__)

DashboardServiceDep = Annotated[
    DashboardService, Depends(lambda: container.get_dashboard_service())
]

@router.post("/rooms/admin-message")
def send_admin_message(
    room_id: Annotated[
        str, Body(..., title="Room ID of the page the user signed up to")
    ],
    message: Annotated[str, Body(..., title="Message to send to user")],
    dashboard_service: DashboardServiceDep,
    api_key: ApiKeyDep,
):
    """Endpoint for sending messages from the admin dashboard."""
    dashboard_service.send_admin_message(room_id, message)
