from fastapi import HTTPException
from pydantic import BaseModel
from typing import Dict
from zootopia.manager.messaging import BirdManager
from zootopia.core.logger import logger
from config.config import config
from zootopia.core.schema import (
    SendVerificationRequest,
    OTPOperationResponse,
    VerifyCodeRequest,
    VerifyCodeResponse,
    ResendVerificationRequest,
)


class SMSOTPService:
    def __init__(self, bird_manager: BirdManager):
        self.bird_sms = bird_manager

    async def send_verification(
        self, request: SendVerificationRequest
    ) -> OTPOperationResponse:
        try:
            self.bird_sms.set_user_phone(request.phone_number)
            self.bird_sms.set_channel_id(config.PHONE_OTP_CHANNEL_ID)
            is_sent, expires_at, verification_id = (
                await self.bird_sms.send_verification(
                    locale=request.locale,
                    max_attempts=request.max_attempts,
                    timeout=request.timeout,
                    code_length=request.code_length,
                )
            )
            return OTPOperationResponse(
                is_sent=is_sent,
                expires_at=expires_at,
                verification_id=verification_id,
            )

        except Exception as e:
            logger.error(f"Error sending verification: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Error sending verification code"
            )

    async def resend_verification(
        self, verification_id: str, request: ResendVerificationRequest
    ) -> OTPOperationResponse:
        try:
            is_sent, expires_at, status = await self.bird_sms.resend_verification(
                verification_id, request.step_index
            )
            return OTPOperationResponse(
                is_sent=is_sent,
                expires_at=expires_at,
                verification_id=verification_id,
            )
        except Exception as e:
            logger.error(f"Error resending verification: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Error resending verification code"
            )

    async def verify_code(
        self, verification_id: str, request: VerifyCodeRequest
    ) -> VerifyCodeResponse:
        try:
            is_verified = await self.bird_sms.verify_code(verification_id, request.code)
            return VerifyCodeResponse(is_verified=is_verified)
        except Exception as e:
            logger.error(f"Error verifying code: {str(e)}")
            raise HTTPException(status_code=500, detail="Error verifying code")
