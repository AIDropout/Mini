from fastapi import APIRouter, Depends, HTTPException, Request, Path
from typing import Annotated

from config.container import container
from mini.api.security import ApiKeyDep
from mini.core.rate_limiter import RateLimiter
from mini.messaging.bird.verification.models import (
    ResendVerificationRequest,
    ResendVerificationResponse,
    SendVerificationRequest,
    SendVerificationResponse,
    VerifyCodeRequest,
    VerifyCodeResponse,
)
from mini.messaging.bird.verification.service import VerifyService

router = APIRouter(prefix="/verifications", tags=["verifications"])

VerifyServiceDep = Annotated[
    VerifyService, Depends(lambda: container.get_verify_service())
]
RateLimiterDep = Annotated[RateLimiter, Depends(lambda: container.get_rate_limiter())]


@router.post("/send")
def send_verification(
    request: SendVerificationRequest,
    http_request: Request,
    verify_service: VerifyServiceDep,
    rate_limiter: RateLimiterDep,
    api_key: ApiKeyDep,
) -> SendVerificationResponse:
    """Start a new SMS OTP verification process."""
    rate_limit_key = f"{request.phone_number}:{http_request.client.host}"
    if not rate_limiter.is_allowed(rate_limit_key):
        raise HTTPException(
            status_code=429, detail="Rate limit exceeded. Try again later."
        )
    return verify_service.send_verification(request)


@router.post("/{verification_id}/resend")
def resend_verification(
    verification_id: Annotated[str, Path(...)],
    request: ResendVerificationRequest,
    verify_service: VerifyServiceDep,
    api_key: ApiKeyDep,
) -> ResendVerificationResponse:
    """Resend an SMS OTP for an existing verification."""
    return verify_service.resend_verification(verification_id, request)


@router.post("/{verification_id}/verify")
def verify_code(
    verification_id: Annotated[str, Path(...)],
    request: VerifyCodeRequest,
    verify_service: VerifyServiceDep,
    api_key: ApiKeyDep,
) -> VerifyCodeResponse:
    """Verify an SMS OTP code for an existing verification."""
    return verify_service.verify_code(verification_id, request)
