from fastapi import APIRouter, Depends, HTTPException, Request, Security

from config.container import container
from mini.api.security import verify_api_key
from mini.core.rate_limiter import RateLimiter
from mini.core.schema.request import (
    ResendVerificationRequest,
    ResendVerificationResponse,
    SendVerificationRequest,
    SendVerificationResponse,
    VerifyCodeRequest,
    VerifyCodeResponse,
)
from mini.service.sms_otp_service import SMSOTPService

router = APIRouter(prefix="/sms-otp", tags=["sms-otp"])


@router.post("/send")
async def send_verification(
    request: SendVerificationRequest,
    http_request: Request,
    sms_otp_service: SMSOTPService = Depends(lambda: container.get_sms_otp_service()),
    rate_limiter: RateLimiter = Depends(lambda: container.get_rate_limiter()),
    api_key: str = Security(verify_api_key),
) -> SendVerificationResponse:
    """Start a new SMS OTP verification process."""
    rate_limit_key = f"{request.phone_number}:{http_request.client.host}"
    if not rate_limiter.is_allowed(rate_limit_key):
        raise HTTPException(
            status_code=429, detail="Rate limit exceeded. Try again later."
        )
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
