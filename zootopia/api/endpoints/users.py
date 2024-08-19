from fastapi import APIRouter, Request, Depends, Security, Path, Body
from pydantic import BaseModel
from config.container import container
from zootopia.api.security import verify_api_key
from zootopia.core.schema.tables import User
import asyncio
import httpx
from config.container import container
from zootopia.service.user_service import UserService
from config.config import config


router = APIRouter()


class UserCreate(BaseModel):
    phone_number: str


@router.post("/users", response_model=User)
async def create_user(
    user: UserCreate,
    user_service: UserService = Depends(lambda: container.get_user_service()),
    api_key: str = Security(verify_api_key),
) -> User:
    return user_service.create_user(user.phone_number)


@router.get("/users/{user_id}", response_model=User)
async def get_user(
    user_id: int = Path(..., title="The ID of the user to get"),
    user_service: UserService = Depends(lambda: container.get_user_service()),
    api_key: str = Security(verify_api_key),
) -> User:
    """Get a user by ID. Returns the retrieved User object"""
    return user_service.get_user(user_id)


@router.patch("/users/{user_id}", response_model=User)
async def update_user(
    user_id: int = Path(..., title="The ID of the user to update"),
    user: User = Body(..., title="The updated user fields"),
    user_service: UserService = Depends(lambda: container.get_user_service()),
    api_key: str = Security(verify_api_key),
) -> User:
    """Update a user. Returns updated User object"""
    return user_service.update_user(user_id=user_id, user_params=user)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int = Path(..., title="The ID of the user to delete"),
    user_service: UserService = Depends(lambda: container.get_user_service()),
    api_key: str = Security(verify_api_key),
) -> None:
    """Delete a user. Returns the id of the deleted user."""
    return user_service.delete_user(user_id)


async def test_user_endpoints():
    TEST_ID = 115  # Change as needed

    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        # Test create_user
        user_data = {"phone_number": "+3142952259"}

        response = await client.post(
            f"/users",
            json=user_data,
            headers={"Authorization": f"Bearer {config.ZOOTOPIA_API_KEY}"},
        )
        print(
            f"POST /users - Status: {response.status_code}, Response: {response.json()}"
        )

        # # Test get_user
        # response = await client.get(
        #     f"/users/{TEST_ID}",
        #     headers={"Authorization": f"Bearer {config.ZOOTOPIA_API_KEY}"},
        # )
        # print(
        #     f"GET /users/{TEST_ID} - Status: {response.status_code}, Response: {response.json()}"
        # )

        # # # Test update_user
        # user_data = {"subscription_status": "inactive"}
        # response = await client.patch(
        #     f"/users/{TEST_ID}",
        #     json=user_data,
        #     headers={"Authorization": f"Bearer {config.ZOOTOPIA_API_KEY}"},
        # )
        # print(
        #     f"PATCH /users/{TEST_ID} - Status: {response.status_code}, Response: {response.json()}"
        # )

        # # # Test delete_user
        # response = await client.delete(
        #     f"/users/{TEST_ID}",
        #     headers={"Authorization": f"Bearer {config.ZOOTOPIA_API_KEY}"},
        # )
        # print(
        #     f"DELETE /users/{TEST_ID} - Status: {response.status_code}, Response: {response.json()}"
        # )


if __name__ == "__main__":
    asyncio.run(test_user_endpoints())
