from typing import Dict, Annotated
from fastapi import APIRouter, Body, Depends, Request, Path

from config.container import container
from mini.api.security import ApiKeyDep
from mini.service.payment_service import PaymentService

router = APIRouter(
    prefix="/payments",
    tags=["payments"],
)

PaymentServiceDep = Annotated[
    PaymentService, Depends(lambda: container.get_payment_service())
]


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    payment_service: PaymentServiceDep,
) -> bool:
    """Processes Stripe events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    payment_service.process_event(payload, sig_header)
    return True


@router.post("/checkout")
def create_checkout_session(
    user_id: Annotated[str, Body(..., title="User")],
    tier: Annotated[str, Body(..., title="basic, pro")],
    payment_service: PaymentServiceDep,
    api_key: ApiKeyDep,
) -> Dict[str, str]:
    """Returns a link that users access to pay for product. Returns {"url": "https://example.com/checkout/session123"}"""
    return payment_service.create_checkout_session(user_id, tier)


@router.get("/portal/{user_id}")
def get_portal_link(
    user_id: Annotated[str, Path(..., title="User ID")],
    payment_service: PaymentServiceDep,
    api_key: ApiKeyDep,
) -> Dict[str, str]:
    """Returns a link for users to manage payment info. Returns {"url": "https://example.com/portal-link"""
    return payment_service.get_portal_link(user_id)
