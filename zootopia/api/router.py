from fastapi import APIRouter
from .endpoints import cron, message, signup, dashboard, phone_otp

router = APIRouter()

router.include_router(cron.router)
router.include_router(message.router)
router.include_router(signup.router)
router.include_router(dashboard.router)
router.include_router(phone_otp.router)

