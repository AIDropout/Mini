from fastapi import APIRouter

from mini.api.endpoints import agents, payment, rooms, sms_otp, users

router = APIRouter()

router.include_router(rooms.router)
router.include_router(payment.router)
router.include_router(sms_otp.router)
router.include_router(users.router)
router.include_router(agents.router)
