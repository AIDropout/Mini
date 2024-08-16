from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class BaseRequest(BaseModel):
    pass


class BaseResponse(BaseModel):
    pass


# Request Schemas
class SignupRequest(BaseRequest):
    agent_id: int
    user_phone: str
    birthday: Optional[str] = None


class SendVerificationRequest(BaseRequest):
    phone_number: str
    locale: str = "en-US"
    max_attempts: int = 3
    timeout: int = 600
    code_length: int = 6


class VerifyCodeRequest(BaseRequest):
    code: str


class ResendVerificationRequest(BaseRequest):
    pass


# Response Schemas
class SendVerificationResponse(BaseResponse):
    is_sent: bool
    expires_at: str
    verification_id: str


class ResendVerificationResponse(BaseResponse):
    is_sent: bool
    is_active: bool
    expires_at: str
    verification_id: str


class VerifyCodeResponse(BaseResponse):
    is_verified: bool
    is_active: bool
