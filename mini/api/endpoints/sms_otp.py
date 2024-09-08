from fastapi import APIRouter, Depends, HTTPException, Request, Path
from typing import Annotated

from config.container import container
from mini.api.security import ApiKeyDep
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

SMSOTPServiceDep = Annotated[
    SMSOTPService, Depends(lambda: container.get_sms_otp_service())
]
RateLimiterDep = Annotated[RateLimiter, Depends(lambda: container.get_rate_limiter())]


@router.post("/send")
def send_verification(
    request: SendVerificationRequest,
    http_request: Request,
    sms_otp_service: SMSOTPServiceDep,
    rate_limiter: RateLimiterDep,
    api_key: ApiKeyDep,
) -> SendVerificationResponse:
    """Start a new SMS OTP verification process."""
    rate_limit_key = f"{request.phone_number}:{http_request.client.host}"
    if not rate_limiter.is_allowed(rate_limit_key):
        raise HTTPException(
            status_code=429, detail="Rate limit exceeded. Try again later."
        )
    return sms_otp_service.send_verification(request)


@router.post("/{verification_id}/resend")
def resend_verification(
    verification_id: Annotated[str, Path(...)],
    request: ResendVerificationRequest,
    sms_otp_service: SMSOTPServiceDep,
    api_key: ApiKeyDep,
) -> ResendVerificationResponse:
    """Resend an SMS OTP for an existing verification."""
    return sms_otp_service.resend_verification(verification_id, request)


@router.post("/{verification_id}/verify")
def verify_code(
    verification_id: Annotated[str, Path(...)],
    request: VerifyCodeRequest,
    sms_otp_service: SMSOTPServiceDep,
    api_key: ApiKeyDep,
) -> VerifyCodeResponse:
    """Verify an SMS OTP code for an existing verification."""
    return sms_otp_service.verify_code(verification_id, request)
