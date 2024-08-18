from fastapi import Depends, APIRouter, Security
from zootopia.api.security import verify_api_key
from zootopia.core.schema import SignupRequest
from config.container import container
from zootopia.service.signup_service import SignupService

router = APIRouter()


@router.post("/signup")
async def signup_webhook(
    request: SignupRequest,
    api_key: str = Security(verify_api_key),
    signup_service: SignupService = Depends(lambda: container.get_signup_service()),
):
    return await signup_service.process_signup(request)
