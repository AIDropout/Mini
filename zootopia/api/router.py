from fastapi import APIRouter
from zootopia.api.endpoints import _signup, rooms, sms_otp, payment, users

router = APIRouter()

router.include_router(rooms.router)
router.include_router(payment.router)
router.include_router(_signup.router)
router.include_router(sms_otp.router)
router.include_router(users.router)