from fastapi import APIRouter

from mini.api.endpoints import agents, payments, rooms, users, verifications, webhooks

router = APIRouter()

router.include_router(rooms.router)
router.include_router(payments.router)
router.include_router(webhooks.router)
router.include_router(users.router)
router.include_router(agents.router)
router.include_router(verifications.router)
