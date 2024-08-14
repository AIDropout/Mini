from fastapi import HTTPException, Depends, APIRouter
from pydantic import BaseModel
from typing import List, Optional
from services.platform.sms.bird import (
    BirdSMSProvider,
)
from zootopia.core.logger import logger
from zootopia.config.env import config

router = APIRouter(prefix="/verify", tags=["verification"])


async def get_bird_sms_provider():
    provider = BirdSMSProvider()
    return provider


class VerificationRequest(BaseModel):
    code: str


class SendVerificationRequest(BaseModel):
    phone_number: str
    locale: str = "en-US"
    max_attempts: int = 3
    timeout: int = 600
    code_length: int = 6


class ResendVerificationRequest(BaseModel):
    step_index: Optional[int] = None


@router.post("/initiate")
async def initiate_verification(
    request: SendVerificationRequest,
    bird_sms: BirdSMSProvider = Depends(get_bird_sms_provider),
):
    """
    - bool: Whether the message was sent successfully
    - str: The expiration time of the verification code
    - str: The verification ID
    """
    try:
        bird_sms.set_user_phone(request.phone_number)
        bird_sms.set_channel_id(config.PHONE_OTP_CHANNEL_ID)
        is_sent, expires_at, verification_id = await bird_sms.send_verification(
            locale=request.locale,
            max_attempts=request.max_attempts,
            timeout=request.timeout,
            code_length=request.code_length,
        )
        return {
            "is_sent": is_sent,
            "expires_at": expires_at,
            "verification_id": verification_id,
        }
    except Exception as e:
        logger.error(f"Error sending verification: {str(e)}")
        raise HTTPException(status_code=500, detail="Error sending verification code")


@router.post("/verify/{verification_id}")
async def verify_code(
    verification_id: str,
    request: VerificationRequest,
    bird_sms: BirdSMSProvider = Depends(get_bird_sms_provider),
):
    try:
        is_verified = await bird_sms.verify_code(verification_id, request.code)
        return {"is_verified": is_verified}
    except Exception as e:
        logger.error(f"Error verifying code: {str(e)}")
        raise HTTPException(status_code=500, detail="Error verifying code")


@router.post("/verify/{verification_id}/resend")
async def resend_verification(
    verification_id: str,
    request: ResendVerificationRequest,
    bird_sms: BirdSMSProvider = Depends(get_bird_sms_provider),
):
    try:
        is_accepted, expires_at, status = await bird_sms.resend_verification(
            verification_id, request.step_index
        )
        return {
            "is_accepted": is_accepted,
            "expires_at": expires_at,
            "status": status,
        }
    except Exception as e:
        logger.error(f"Error resending verification: {str(e)}")
        raise HTTPException(status_code=500, detail="Error resending verification code")
