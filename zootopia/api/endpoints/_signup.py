from fastapi import Depends, APIRouter, Security
from zootopia.api.security import verify_api_key
from config.container import container
from zootopia.service.signup_service import SignupService
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class SignupRequest(BaseModel):
    agent_id: str
    user_phone: str
    birthday: Optional[str] = None


@router.post("/signup")
async def signup_webhook(
    request: SignupRequest,
    api_key: str = Security(verify_api_key),
    signup_service: SignupService = Depends(lambda: container.get_signup_service()),
):
    return await signup_service.process_signup(request)
