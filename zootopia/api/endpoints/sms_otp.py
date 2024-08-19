from fastapi import Depends, APIRouter, Security
from zootopia.core.schema.request import (
    SendVerificationRequest,
    SendVerificationResponse,
    ResendVerificationRequest,
    ResendVerificationResponse,
    VerifyCodeRequest,
    VerifyCodeResponse,
)
from zootopia.api.security import verify_api_key
from config.container import container
from zootopia.service.sms_otp_service import SMSOTPService

router = APIRouter(prefix="/sms-otp", tags=["sms-otp"])


@router.post("/send")
async def send_verification(
    request: SendVerificationRequest,
    sms_otp_service: SMSOTPService = Depends(lambda: container.get_sms_otp_service()),
    api_key: str = Security(verify_api_key),
) -> SendVerificationResponse:
    """Start a new SMS OTP verification process."""
    return await sms_otp_service.send_verification(request)


@router.post("/{verification_id}/resend")
async def resend_verification(
    verification_id: str,
    request: ResendVerificationRequest,
    sms_otp_service: SMSOTPService = Depends(lambda: container.get_sms_otp_service()),
    api_key: str = Security(verify_api_key),
) -> ResendVerificationResponse:
    """Resend an SMS OTP for an existing verification."""
    return await sms_otp_service.resend_verification(verification_id, request)


@router.post("/{verification_id}/verify")
async def verify_code(
    verification_id: str,
    request: VerifyCodeRequest,
    sms_otp_service: SMSOTPService = Depends(lambda: container.get_sms_otp_service()),
    api_key: str = Security(verify_api_key),
) -> VerifyCodeResponse:
    """Verify an SMS OTP code for an existing verification."""
    return await sms_otp_service.verify_code(verification_id, request)
