from fastapi import APIRouter, Body, Depends, Path, Security
from fastapi.responses import JSONResponse
from typing import List

from config.container import container
from mini.api.security import verify_api_key
from mini.core.schema.tables import Room, User
from mini.service.user_service import UserService

router = APIRouter()

@router.post("/users", response_model=User)
async def create_user(
    id: str = Body(..., title="UUID that Supabase Auth created on the frontend"),
    phone_number: str = Body(..., title="The phone number of the new user"),
    user_service: UserService = Depends(lambda: container.get_user_service()),
    api_key: str = Security(verify_api_key),
) -> User:
    return user_service.create_user(id=id, phone_number=phone_number)

@router.get("/users/{user_id}/rooms", response_model=List[Room])
def get_user_rooms(
    user_id: str = Path(..., title="The ID of the user to get"),
    user_service: UserService = Depends(lambda: container.get_user_service()),
    api_key: str = Security(verify_api_key),
) -> List[Room]:
    return user_service.get_user_rooms(user_id)

@router.get("/users/{user_id}", response_model=User)
async def get_user(
    user_id: str = Path(..., title="The ID of the user to get"),
    user_service: UserService = Depends(lambda: container.get_user_service()),
    api_key: str = Security(verify_api_key),
) -> User:
    return user_service.get_user(user_id)

@router.patch("/users/{user_id}", response_model=User)
async def update_user(
    user_id: str = Path(..., title="The ID of the user to update"),
    user_update: dict = Body(..., title="The fields to update"),
    user_service: UserService = Depends(lambda: container.get_user_service()),
    api_key: str = Security(verify_api_key),
) -> User:
    return user_service.update_user(user_id=user_id, user_params=user_update)

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str = Path(..., title="The ID of the user to delete"),
    user_service: UserService = Depends(lambda: container.get_user_service()),
    api_key: str = Security(verify_api_key),
) -> JSONResponse:
    return user_service.delete_user(user_id)