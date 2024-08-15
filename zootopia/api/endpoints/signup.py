from fastapi import APIRouter, Security
from zootopia.api.security import verify_api_key
from zootopia.core.schema import SignupRequest
from zootopia.service import SignupService

router = APIRouter()


@router.post("/signup")
async def signup_webhook(
    request: SignupRequest, api_key: str = Security(verify_api_key)
):
    signup_service = SignupService()
    return await signup_service.process_signup(request)
