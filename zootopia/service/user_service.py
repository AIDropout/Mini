# services/room_service.py
from fastapi import HTTPException
from zootopia.manager.database import DatabaseManager
from zootopia.manager.payment.customer import CustomerManager
from zootopia.core.schema.tables import Tables, User
from zootopia.service.base import Service
from fastapi.responses import JSONResponse


class UserService(Service):
    def __init__(
        self, database_manager: DatabaseManager, customer_manager: CustomerManager
    ):
        super().__init__(database_manager)
        self.customer_manager = customer_manager

    def create_user(self, phone_number: str) -> User:
        customer = self.customer_manager.create_customer(phone=phone_number)
        new_user = self.database_manager.insert(
            table_name=Tables.USERS,
            item=User(phone_number=phone_number, customer_id=customer.id),
        )
        if not new_user:
            raise HTTPException(status_code=404, detail="User not created")
        return new_user

    def get_user(self, user_id: int) -> User:
        user = self.database_manager.get_row(Tables.USERS, {Tables.USERS__id: user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def update_user(self, user_id, user_params) -> User:
        existing_user = self.database_manager.get_row(
            Tables.USERS, {Tables.USERS__id: user_id}
        )
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")

        updated_user = self.database_manager.update(
            table_name=Tables.USERS,
            item=user_params,
            condition_key=Tables.USERS__id,
            condition_value=user_id,
        )
        if not updated_user:
            raise HTTPException(status_code=400, detail="Failed to update user")
        return updated_user

    def delete_user(self, user_id) -> None:
        """Delete a user. Returns the id of the deleted user."""
        existing_user = self.database_manager.get_row(
            Tables.USERS, {Tables.USERS__id: user_id}
        )
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")

        deleted_user_id = self.database_manager.delete(
            Tables.USERS, {Tables.USERS__id: user_id}
        )
        if not deleted_user_id:
            raise HTTPException(status_code=400, detail="Failed to delete user")
        return JSONResponse(status_code=200, content="Succesfully deleted user")
