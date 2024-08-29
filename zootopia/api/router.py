from fastapi import APIRouter
from zootopia.api.endpoints import rooms, users, sms_otp, payment, agents

router = APIRouter()

router.include_router(rooms.router)
router.include_router(payment.router)
router.include_router(sms_otp.router)
router.include_router(users.router)
router.include_router(agents.router)
