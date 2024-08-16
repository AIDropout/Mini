from enum import Enum

class VerificationStatus(Enum):
    ACCEPTED = "accepted"
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELED = "canceled"

class ErrorCode(Enum):
    VERIFICATION_CODE_MISMATCH = "VerificationCodeMismatch"
    MAX_ATTEMPTS_REACHED = "MaxAttemptsReached"
    