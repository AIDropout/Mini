from fastapi import APIRouter, Depends, HTTPException
from zootopia.manager.database.database import DatabaseManager
from config.container import container
from zootopia.core.schema.tables import User

router = APIRouter()

def get_db_manager():
    return container.database_manager

@router.get("/profile/{phone_number}", response_model=User)
async def get_user_profile(
    phone_number: str, 
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    user = db_manager.get_row("users", {"phone_number": phone_number})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user