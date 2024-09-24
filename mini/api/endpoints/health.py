from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])

class HealthResponse(BaseModel):
    status: str

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Perform a health check
    """
    return HealthResponse(status="OK")