from fastapi import (
    APIRouter,
    Request,
    BackgroundTasks,
    HTTPException,
    Security,
    Depends,
    Body,
)
from zootopia.service.reply_service import ReplyService
from zootopia.service.cron_service import CronService
from zootopia.service.dashboard_service import DashboardService
from zootopia.api.security import verify_api_key
from zootopia.utils.utils import is_ngrok_url
from zootopia.core.logger import logger
from config.container import container
from zootopia.service.room_service import RoomService
from typing import Optional
from pydantic import BaseModel
from zootopia.core.schema.tables import Room

router = APIRouter()


class CreateRoomRequest(BaseModel):
    agent_id: str
    user_id: str


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
        reply_service.handle_respond(request_body)
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
    request: Request,
    dashboard_service: DashboardService = Depends(
        lambda: container.get_dashboard_service()
    ),
    api_key: str = Security(verify_api_key),
):
    """Endpoint for sending messages from the admin dashboard."""
    try:
        payload = await request.json()
        await dashboard_service.send_admin_message(payload)
        return {"status": "Admin message sent successfully"}
    except Exception as e:
        logger.exception("Error in send_admin_message")
        raise HTTPException(status_code=500, detail=str(e))


async def test_room_endpoints():

    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        # Test create_room
        room_data = {
            "agent_id": "f49c9af0-929b-4fe1-9522-6fe4a325bdf5",
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
        }

        response = await client.post(
            "/rooms",
            json=room_data,
            headers={"Authorization": f"Bearer {config.ZOOTOPIA_API_KEY}"},
        )
        print(
            f"POST /rooms - Status: {response.status_code}, Response: {response.json()}"
        )

        if response.status_code == 200:
            created_room = response.json()
            room_id = created_room.get("id")

            # Test get_room (if you have this endpoint)
            # response = await client.get(
            #     f"/rooms/{room_id}",
            #     headers={"Authorization": f"Bearer {config.ZOOTOPIA_API_KEY}"},
            # )
            # print(f"GET /rooms/{room_id} - Status: {response.status_code}, Response: {response.json()}")

            # Test update_room (if you have this endpoint)
            # update_data = {"some_field": "new_value"}
            # response = await client.patch(
            #     f"/rooms/{room_id}",
            #     json=update_data,
            #     headers={"Authorization": f"Bearer {config.ZOOTOPIA_API_KEY}"},
            # )
            # print(f"PATCH /rooms/{room_id} - Status: {response.status_code}, Response: {response.json()}")

            # Test delete_room (if you have this endpoint)
            # response = await client.delete(
            #     f"/rooms/{room_id}",
            #     headers={"Authorization": f"Bearer {config.ZOOTOPIA_API_KEY}"},
            # )
            # print(f"DELETE /rooms/{room_id} - Status: {response.status_code}, Response: {response.json()}")


if __name__ == "__main__":
    import httpx
    import asyncio
    from config.config import config

    asyncio.run(test_room_endpoints())
