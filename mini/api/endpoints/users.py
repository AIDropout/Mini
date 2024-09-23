from fastapi import APIRouter, Body, Depends, Path, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Annotated

from config.container import container
from mini.api.security import ApiKeyDep
from mini.database.models import Room, User
from mini.database.service.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

UserServiceDep = Annotated[UserService, Depends(lambda: container.get_user_service())]


@router.post("/", response_model=User)
def create_user(
    id: Annotated[
        str, Body(..., title="UUID that Supabase Auth created on the frontend")
    ],
    phone_number: Annotated[str, Body(..., title="The phone number of the new user")],
    user_service: UserServiceDep,
    background_tasks: BackgroundTasks,
    api_key: ApiKeyDep,
) -> User:
    return user_service.create_user(
        id=id, phone_number=phone_number, background_tasks=BackgroundTasks
    )


@router.get("/{user_id}", response_model=User)
def get_user(
    user_id: Annotated[str, Path(..., title="The ID of the user to get")],
    user_service: UserServiceDep,
    api_key: ApiKeyDep,
) -> User:
    return user_service.get_user(user_id)


@router.get("/{user_id}/rooms", response_model=List[Room])
def get_user_rooms(
    user_id: Annotated[str, Path(..., title="The ID of the user to get")],
    user_service: UserServiceDep,
    api_key: ApiKeyDep,
) -> List[Room]:
    """Gets all rooms that a user is in"""
    return user_service.get_user_rooms(user_id)


@router.patch("/{user_id}", response_model=User)
def update_user(
    user_id: Annotated[str, Path(..., title="The ID of the user to update")],
    user_update: Annotated[
        dict,
        Body(..., title="The fields to update. Only the updated fields are needed."),
    ],
    user_service: UserServiceDep,
    api_key: ApiKeyDep,
) -> User:
    return user_service.update_user(user_id=user_id, update_data=user_update)


@router.delete("/{user_id}")
def delete_user(
    user_id: Annotated[str, Path(..., title="The ID of the user to delete.")],
    user_service: UserServiceDep,
    api_key: ApiKeyDep,
) -> JSONResponse:
    return user_service.delete_user(user_id)
