from fastapi import APIRouter
from zootopia.api.endpoints import room, signup, sms_otp, payment

router = APIRouter()

router.include_router(room.router)
router.include_router(payment.router)
router.include_router(signup.router)
router.include_router(sms_otp.router)