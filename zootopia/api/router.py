from fastapi import APIRouter
from zootopia.api.endpoints import room, signup, signin, sms_otp, payment, user

router = APIRouter()

router.include_router(room.router)
router.include_router(payment.router)
router.include_router(signup.router)
router.include_router(signin.router)
router.include_router(sms_otp.router)
router.include_router(user.router)