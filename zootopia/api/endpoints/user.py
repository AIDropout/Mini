from fastapi import APIRouter, Request, Depends, Security, Path, Body, HTTPException
from pydantic import BaseModel, Field
from zootopia.service.payment_service import PaymentService
from config.container import container
from typing import Dict
from zootopia.api.security import verify_api_key
from zootopia.manager.database.database import DatabaseManager
from zootopia.core.schema import User


router = APIRouter(
    tags=["users"],
)

def get_db_manager():
    return container.database_manager

@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: int = Path(..., title="The ID of the user to get"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    user = db_manager.get_row("users", {"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

class UserUpdate(BaseModel):
    name: str
    email: str

@router.patch("/{user_id}")
async def update_user(
    user_id: int = Path(..., title="The ID of the user to update"),
    user: UserUpdate = Body(..., title="The updated user information"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    # Implementation needed
    raise NotImplementedError

@router.delete("/{user_id}")
async def delete_user(
    user_id: int = Path(..., title="The ID of the user to delete"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    # Implementation needed
    raise NotImplementedError

@router.get("/profile/{phone_number}", response_model=User)
async def get_user_profile(
    phone_number: str, 
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    print(phone_number, "this is phone number")
    normalized_phone = ''.join(filter(str, phone_number))
    user = db_manager.get_row("users", {"phone_number": normalized_phone})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user