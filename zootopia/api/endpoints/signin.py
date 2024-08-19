from fastapi import APIRouter, Depends, HTTPException
from zootopia.manager.database.database import DatabaseManager
from config.container import container

router = APIRouter()

def get_db_manager():
    return container.database_manager

@router.get("/verify-phone-number/{phone_number}")
async def verify_phone_number(
    phone_number: str, 
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    # Normalize the phone number (remove spaces, dashes, etc.)
    normalized_phone = ''.join(filter(str, phone_number))
    
    # Check if the normalized phone number exists
    exists = db_manager.phone_number_exists(normalized_phone)
    
    if not exists:
        # Log the attempt for debugging
        print(f"Phone number not found: {normalized_phone}")
        
    return {"exists": exists}