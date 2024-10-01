from fastapi import HTTPException

from config.config import config
from mini.core.logger import get_logger
from mini.core.enums import MessagingProviderType
from mini.messaging.providers.bird.verification.models import (
    ResendVerificationRequest,
    ResendVerificationResponse,
    SendVerificationRequest,
    SendVerificationResponse,
    VerifyCodeRequest,
    VerifyCodeResponse,
)
from mini.messaging.providers import messaging_providers

logger = get_logger(__name__)


class VerifyService:
    def __init__(self):
        self.bird_sms = messaging_providers.get(MessagingProviderType.BIRD)
        if self.bird_sms is None:
            logger.error("Bird messaging provider is not available.")
            raise HTTPException(
                status_code=500, detail="Bird messaging provider is not available."
            )

    def send_verification(
        self, request: SendVerificationRequest
    ) -> SendVerificationResponse:
        try:
            self.bird_sms.set_receiver(request.phone_number)
            self.bird_sms.set_sender(config.PHONE_OTP_CHANNEL_ID)
            is_sent, expires_at, verification_id = self.bird_sms.send_verification(
                locale=request.locale,
                max_attempts=request.max_attempts,
                timeout=request.timeout,
                code_length=request.code_length,
            )
            print(is_sent)
            return SendVerificationResponse(
                is_sent=is_sent,
                expires_at=expires_at,
                verification_id=verification_id,
            )

        except Exception as e:
            logger.error(f"Error sending verification: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Error sending verification code"
            )

    def resend_verification(
        self, verification_id: str, request: ResendVerificationRequest
    ) -> ResendVerificationResponse:
        try:
            is_sent, is_active, expires_at = self.bird_sms.resend_verification(
                verification_id
            )
            return ResendVerificationResponse(
                is_sent=is_sent,
                is_active=is_active,
                expires_at=expires_at,
                verification_id=verification_id,
            )
        except Exception as e:
            logger.error(f"Error resending verification: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Error resending verification code"
            )

    def verify_code(
        self, verification_id: str, request: VerifyCodeRequest
    ) -> VerifyCodeResponse:
        try:
            is_verified, is_active = self.bird_sms.verify_code(
                verification_id, request.code
            )
            return VerifyCodeResponse(is_verified=is_verified, is_active=is_active)
        except Exception as e:
            logger.error(f"Error verifying code: {str(e)}")
            raise HTTPException(status_code=500, detail="Error verifying code")
