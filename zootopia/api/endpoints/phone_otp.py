from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from services.platform.sms.bird import (
    BirdSMSProvider,
)
from zootopia.core.logger import logger
from zootopia.config.env import config

app = FastAPI()


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


@app.post("/verify/initiate")
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


@app.post("/verify/{verification_id}")
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
