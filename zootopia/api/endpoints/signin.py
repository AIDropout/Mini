from fastapi import APIRouter, Depends
from zootopia.manager.database.database import DatabaseManager
from config.container import container

router = APIRouter()

def get_db_manager():
    return container.database_manager

@router.get("/verify-signin/{phone_number}")
async def verify_phone_number(
    phone_number: str, 
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    exists = db_manager.phone_number_exists(phone_number)
    return {"exists": exists}