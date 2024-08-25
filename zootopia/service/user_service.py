from fastapi import HTTPException
from zootopia.manager.database import DatabaseManager
from zootopia.manager.payment.customer import CustomerManager
from zootopia.core.schema.tables import Tables, User, Room
from zootopia.core.schema.subscription import SubscriptionStatus
from zootopia.service.base import Service
from fastapi.responses import JSONResponse
from postgrest.exceptions import APIError
from typing import List


class UserService(Service):
    def __init__(
        self, database_manager: DatabaseManager, customer_manager: CustomerManager
    ):
        super().__init__(database_manager)
        self.customer_manager = customer_manager

    def create_user(self, id: str, phone_number: str) -> User:
        try:
            customer = self.customer_manager.create_customer(phone=phone_number)
            new_user = self.database_manager.insert(
                table_name=Tables.USERS,
                item=User(id=id, phone_number=phone_number, customer_id=customer.id),
            )
            if new_user is None:
                raise HTTPException(status_code=500, detail="Failed to create user")
            return new_user
        except APIError as e:
            if "users_phone_number_key" in str(e):
                raise HTTPException(
                    status_code=409, detail="User with this phone number already exists"
                )
            raise HTTPException(status_code=500, detail="Error creating user")

    def get_user(self, id: str) -> User:
        user = self.database_manager.get_row(Tables.USERS, {Tables.USERS__id: id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def update_user(self, id: str, user_params) -> User:
        existing_user = self.database_manager.get_row(
            Tables.USERS, {Tables.USERS__id: id}
        )
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")

        updated_user = self.database_manager.update(
            table_name=Tables.USERS,
            item=user_params,
            condition_key=Tables.USERS__id,
            condition_value=id,
        )
        if not updated_user:
            raise HTTPException(status_code=400, detail="Failed to update user")
        return updated_user

    def delete_user(self, id: str) -> None:
        """Delete a user. Returns the id of the deleted user."""
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
        return JSONResponse(status_code=200, content="Succesfully deleted user")

    def get_user_rooms(self, user_id: str) -> List[Room]:
        """Get all rooms that a user is in"""
        rooms = self.database_manager.get_multiple_rows(
            table_name=Tables.ROOMS,
            conditions={Tables.ROOMS__user_id: user_id},
        )

        if not rooms:
            raise HTTPException(
                status_code=404, detail="User does not have any rooms with any agents"
            )

        return rooms
