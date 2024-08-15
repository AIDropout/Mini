from fastapi import Depends, APIRouter, Security
from typing import Annotated
from zootopia.core.schema import (
    InitiateVerificationRequest,
    InitiateVerificationResponse,
    VerifyCodeRequest,
    VerifyCodeResponse,
    ResendVerificationRequest,
)
from zootopia.service import SMSOTPService
from zootopia.api.security import verify_api_key

router = APIRouter(prefix="/sms-otp", tags=["sms-otp"])


async def get_sms_otp_service():
    return SMSOTPService()


SMSOTPServiceDep = Annotated[SMSOTPService, Depends(get_sms_otp_service)]


@router.post("/initiate")
async def initiate_verification(
    request: InitiateVerificationRequest,
    sms_otp_service: SMSOTPServiceDep,
    api_key: str = Security(verify_api_key),
) -> InitiateVerificationResponse:
    """Initiate a new SMS OTP verification process."""
    return await sms_otp_service.initiate_verification(request)


@router.patch("/{verification_id}/verify")
async def verify_code(
    verification_id: str,
    request: VerifyCodeRequest,
    sms_otp_service: SMSOTPServiceDep,
    api_key: str = Security(verify_api_key),
) -> VerifyCodeResponse:
    """Verify an SMS OTP code for an existing verification."""
    return await sms_otp_service.verify_code(verification_id, request)


@router.patch("/{verification_id}/resend")
async def resend_verification(
    verification_id: str,
    request: ResendVerificationRequest,
    sms_otp_service: SMSOTPServiceDep,
    api_key: str = Security(verify_api_key),
) -> ResendVerificationRequest:
    """Resend an SMS OTP for an existing verification."""
    return await sms_otp_service.resend_verification(verification_id, request)
