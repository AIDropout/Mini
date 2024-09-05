from typing import List, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    HTTPException,
    Path,
    Request,
    Security,
)
from pydantic import BaseModel

from config.container import container
from mini.api.security import verify_api_key
from mini.core.logger import get_logger
from mini.core.schema.tables import Room
from mini.service.cron_service import CronService
from mini.service.dashboard_service import DashboardService
from mini.service.reply_service import ReplyService
from mini.service.room_service import RoomService
from mini.utils.utils import is_ngrok_url

router = APIRouter()
logger = get_logger(__name__)

@router.get("/rooms/{user_id}")
async def get_rooms(
    user_id: str = Path(..., title="The user's ID"),
    room_service: RoomService = Depends(lambda: container.get_room_service()),
    api_key: str = Security(verify_api_key),
) -> Room:
    """Creates a room and sends the first message to the user"""
    return await room_service.get_user_rooms(user_id=user_id)


@router.post("/rooms")
async def create_room(
    agent_id: str = Body(..., title="Agent ID of the page the user signed up to"),
    user_id: str = Body(..., title="The user's ID"),
    room_service: RoomService = Depends(lambda: container.get_room_service()),
    api_key: str = Security(verify_api_key),
) -> Room:
    """Creates a room and sends the first message to the user"""
    return await room_service.create_room(agent_id=agent_id, user_id=user_id)


@router.post("/rooms/respond")
async def respond_webhook(
    request: Request,
    reply_service: ReplyService = Depends(lambda: container.get_reply_service()),
):
    """Endpoint hit by incoming user messages."""
    try:
        request_body = await request.json()
        await reply_service.handle_respond(request_body)
        return {"status": "Message received and processing scheduled"}
    except Exception as e:
        logger.exception("Error in respond_webhook")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rooms/revive")
async def revive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    cron_service: CronService = Depends(lambda: container.get_cron_service()),
    api_key: str = Security(verify_api_key),
):
    """Endpoint hit by Supabase cron job every x minutes."""
    try:
        await cron_service.refresh_rooms(
            background_tasks, dev_mode=is_ngrok_url(str(request.base_url))
        )
        return {"status": "Revive process initiated"}
    except Exception as e:
        logger.exception(f"Error in revive webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rooms/admin-message")
async def send_admin_message(
    room_id: str = Body(..., title="Room ID of the page the user signed up to"),
    message: str = Body(..., title="Message to send to user"),
    dashboard_service: DashboardService = Depends(
        lambda: container.get_dashboard_service()
    ),
    api_key: str = Security(verify_api_key),
):
    """Endpoint for sending messages from the admin dashboard."""
    try:
        await dashboard_service.send_admin_message(room_id, message)
        return {"status": "Admin message sent successfully"}
    except Exception as e:
        logger.exception("Error in send_admin_message")
        raise HTTPException(status_code=500, detail=str(e))


async def test_room_endpoints():

    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        # Test create_room
        room_data = {
            "agent_id": "6e37a9d5-4426-4f05-ad31-3918392ad58a",
            "user_id": "946f4f9d-1111-495e-b59d-5f3704deb11b",
        }

        response = await client.post(
            "/rooms",
            json=room_data,
            headers={"Authorization": f"Bearer {config.BACKEND_API_KEY}"},
        )
        print(
            f"POST /rooms - Status: {response.status_code}, Response: {response.json()}"
        )

        if response.status_code == 200:
            created_room = response.json()
            room_id = created_room.get("id")
            user_id = room_data["user_id"]

            # Test get_user_agent
            response = await client.get(
                f"/rooms/agent/{user_id}",
                headers={"Authorization": f"Bearer {config.BACKEND_API_KEY}"},
            )
            print(
                f"GET /rooms/agent/{user_id} - Status: {response.status_code}, Response: {response.json()}"
            )

            # Test get_room (if you have this endpoint)
            # response = await client.get(
            #     f"/rooms/{room_id}",
            #     headers={"Authorization": f"Bearer {config.BACKEND_API_KEY}"},
            # )
            # print(f"GET /rooms/{room_id} - Status: {response.status_code}, Response: {response.json()}")

            # Test update_room (if you have this endpoint)
            # update_data = {"some_field": "new_value"}
            # response = await client.patch(
            #     f"/rooms/{room_id}",
            #     json=update_data,
            #     headers={"Authorization": f"Bearer {config.BACKEND_API_KEY}"},
            # )
            # print(f"PATCH /rooms/{room_id} - Status: {response.status_code}, Response: {response.json()}")

            # Test delete_room (if you have this endpoint)
            # response = await client.delete(
            #     f"/rooms/{room_id}",
            #     headers={"Authorization": f"Bearer {config.BACKEND_API_KEY}"},
            # )
            # print(f"DELETE /rooms/{room_id} - Status: {response.status_code}, Response: {response.json()}")


if __name__ == "__main__":
    import asyncio

    import httpx

    from config.config import config

    asyncio.run(test_room_endpoints())
