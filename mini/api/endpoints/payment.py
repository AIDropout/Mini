from typing import Dict

from fastapi import APIRouter, Body, Depends, Request, Security

from config.container import container
from mini.api.security import verify_api_key
from mini.service.payment_service import PaymentService

router = APIRouter(
    prefix="/payment",
    tags=["payment"],
)


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    payment_service: PaymentService = Depends(lambda: container.get_payment_service()),
) -> bool:
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    payment_service.process_event(payload, sig_header)
    return True


@router.post("/checkout")
def create_checkout_session(
    user_id: str = Body(..., title="User"),
    tier: str = Body(..., title="Basic, Pro, VIP"),
    payment_service: PaymentService = Depends(lambda: container.get_payment_service()),
    api_key: str = Security(verify_api_key),
) -> Dict[str, str]:
    """Returns {"url": "https://example.com/checkout/session123"}"""
    return payment_service.create_checkout_session(user_id, tier)


@router.get("/portal/{user_id}")
def get_portal_link(
    user_id: str,
    payment_service: PaymentService = Depends(lambda: container.get_payment_service()),
    api_key: str = Security(verify_api_key),
) -> Dict[str, str]:
    """Returns {"url": "https://example.com/portal-link"""
    return payment_service.get_portal_link(user_id)
