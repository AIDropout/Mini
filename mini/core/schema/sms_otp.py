from enum import Enum


class VerificationStatus(Enum):
    """Bird statuses"""

    ACCEPTED = "accepted"
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELED = "canceled"


class ErrorCode(Enum):
    """Bird API errors"""

    VERIFICATION_CODE_MISMATCH = "VerificationCodeMismatch"
    MAX_ATTEMPTS_REACHED = "MaxAttemptsReached"
    UNEXPECTED_VERIFICATION_STATUS = "UnexpectedVerificationStatus"
