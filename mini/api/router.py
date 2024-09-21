from fastapi import APIRouter

from mini.api.endpoints import agents, payments, rooms, sms_otp, users
from mini.api.endpoints.webhooks import instagram

router = APIRouter()

router.include_router(rooms.router)
router.include_router(payments.router)
router.include_router(sms_otp.router)
router.include_router(users.router)
router.include_router(agents.router)
router.include_router(instagram.router, prefix="/webhooks")

