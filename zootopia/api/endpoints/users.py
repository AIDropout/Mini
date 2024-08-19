from fastapi import APIRouter, Request, Depends, Security, Path, Body, HTTPException
from pydantic import BaseModel
from config.container import container
from zootopia.api.security import verify_api_key
from zootopia.manager.database import DatabaseManager
from zootopia.core.schema.tables import Tables, User
import asyncio
import httpx
from config.config import config
from fastapi.responses import JSONResponse

router = APIRouter()


def get_database_manager():
    return container.database_manager


@router.get("/users/{user_id}", response_model=User)
async def get_user(
    user_id: int = Path(..., title="The ID of the user to get"),
    database_manager: DatabaseManager = Depends(lambda: get_database_manager()),
    api_key: str = Security(verify_api_key),
) -> User:
    """Get a user by ID. Returns the retrieved User object"""
    user = database_manager.get_row(
        Tables.USERS.value, {Tables.USERS__id.value: user_id}
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/users/{phone_number}", response_model=User)
async def get_user(
    phone_number: str = Path(..., title="The phone number of the user to get"),
    database_manager: DatabaseManager = Depends(lambda: get_database_manager()),
    api_key: str = Security(verify_api_key),
) -> User:
    """Get a user by ID. Returns the retrieved User object"""
    user = database_manager.get_row(
        Tables.USERS.value, {Tables.USERS__phone_number.value: phone_number}
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/users/{user_id}", response_model=User)
async def update_user(
    user_id: int = Path(..., title="The ID of the user to update"),
    user: User = Body(..., title="The updated user object"),
    database_manager: DatabaseManager = Depends(lambda: get_database_manager()),
    api_key: str = Security(verify_api_key),
) -> User:
    """Update a user. Returns updated User object"""
    existing_user = database_manager.get_row(
        Tables.USERS.value, {Tables.USERS__id.value: user_id}
    )
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    updated_user = database_manager.update(
        table_name=Tables.USERS.value,
        item=user,
        condition_key=Tables.USERS__id.value,
        condition_value=user_id,
    )
    if not updated_user:
        raise HTTPException(status_code=400, detail="Failed to update user")
    return updated_user


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int = Path(..., title="The ID of the user to delete"),
    database_manager: DatabaseManager = Depends(lambda: get_database_manager()),
    api_key: str = Security(verify_api_key),
) -> None:
    """Delete a user. Returns the id of the deleted user."""
    existing_user = database_manager.get_row(
        Tables.USERS.value, {Tables.USERS__id.value: user_id}
    )
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    deleted_user_id = database_manager.delete(
        Tables.USERS.value, {Tables.USERS__id.value: user_id}
    )
    if not deleted_user_id:
        raise HTTPException(status_code=400, detail="Failed to delete user")
    return JSONResponse(status_code=200, content="Succesfully deleted user")


async def test_user_endpoints():
    TEST_ID = 113  # Change as needed

    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        # Test get_user
        response = await client.get(
            f"/users/{TEST_ID}",
            headers={"Authorization": f"Bearer {config.ZOOTOPIA_API_KEY}"},
        )
        print(
            f"GET /users/{TEST_ID} - Status: {response.status_code}, Response: {response.json()}"
        )

        # # Test update_user
        user_data = {"subscription_status": "inactive"}
        response = await client.patch(
            f"/users/{TEST_ID}",
            json=user_data,
            headers={"Authorization": f"Bearer {config.ZOOTOPIA_API_KEY}"},
        )

        print(
            f"PATCH /users/{TEST_ID} - Status: {response.status_code}, Response: {response.json()}"
        )

        # # Test delete_user
        response = await client.delete(
            f"/users/{TEST_ID}",
            headers={"Authorization": f"Bearer {config.ZOOTOPIA_API_KEY}"},
        )
        print(
            f"DELETE /users/{TEST_ID} - Status: {response.status_code}, Response: {response.json()}"
        )


if __name__ == "__main__":
    asyncio.run(test_user_endpoints())
