from fastapi import APIRouter
from .endpoints import cron, message, signup, dashboard

router = APIRouter()

router.include_router(cron.router)
router.include_router(message.router)
router.include_router(signup.router)
router.include_router(dashboard.router)