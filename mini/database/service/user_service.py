from typing import Any, Dict, List

from fastapi import HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from postgrest.exceptions import APIError

from config.config import config
from mini.database.models import Room, Tables, User
from mini.database.database import DatabaseManager
from mini.messaging.providers.discord import discord_manager
from mini.utils.utils import get_infostring
from mini.payment.stripe.customer import CustomerManager


class UserService:
    def __init__(
        self, database_manager: DatabaseManager, customer_manager: CustomerManager
    ):
        self.database_manager = database_manager
        self.customer_manager = customer_manager

    def create_user(
        self, id: str, phone_number: str, background_tasks: BackgroundTasks
    ) -> User:
        try:
            customer = self.customer_manager.create_customer(phone=phone_number)
            new_user = self.database_manager.insert(
                table_name=Tables.USERS,
                item=User(id=id, phone_number=phone_number, customer_id=customer.id),
            )
            if new_user is None:
                raise HTTPException(status_code=500, detail="Failed to create user")

            if config.ENVIRONMENT == "production":
                background_tasks.add_task(
                    discord_manager.log_website_activity,
                    f"-# **New signup**: {phone_number} {get_infostring()}",
                )

            return new_user
        except APIError as e:
            if "users_phone_number_key" in str(e):
                raise HTTPException(
                    status_code=409, detail="User with this phone number already exists"
                )
            raise HTTPException(
                status_code=500, detail=f"Error creating user: {str(e)}"
            )

    def get_user(self, id: str) -> User:
        user = self.database_manager.get_row(Tables.USERS, {Tables.USERS__id: id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> User:
        existing_user = self.database_manager.get_row(
            Tables.USERS, {Tables.USERS__id: user_id}
        )
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")

        update_data = {k: v for k, v in update_data.items() if v is not None}

        updated_user = self.database_manager.update(
            table_name=Tables.USERS,
            update_data=update_data,
            condition_key=Tables.USERS__id,
            condition_value=user_id,
        )
        if not updated_user:
            raise HTTPException(status_code=400, detail="Failed to update user")
        return updated_user

    def delete_user(self, id: str) -> JSONResponse:
        existing_user = self.database_manager.get_row(
            Tables.USERS, {Tables.USERS__id: id}
        )
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")

        deleted_user_id = self.database_manager.delete(
            Tables.USERS, {Tables.USERS__id: id}
        )
        if not deleted_user_id:
            raise HTTPException(status_code=400, detail="Failed to delete user")
        return JSONResponse(status_code=200, content="Successfully deleted user")

    def get_user_rooms(self, user_id: str) -> List[Room]:
        rooms = self.database_manager.get_multiple_rows(
            table_name=Tables.ROOMS,
            conditions={Tables.ROOMS__user_id: user_id},
        )
        return rooms
