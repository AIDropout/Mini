from fastapi import APIRouter, Request, Depends, Security
from pydantic import BaseModel, Field
from zootopia.service.payment_service import PaymentService
from config.container import container
from typing import Dict
from zootopia.api.security import verify_api_key

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
    await payment_service.process_event(payload, sig_header)
    return True


class Checkout(BaseModel):
    user_id: str = Field(..., description="Unique identifier of the user.")


@router.post("/checkout")
async def create_checkout_session(
    data: Checkout,
    request: Request,
    payment_service: PaymentService = Depends(lambda: container.get_payment_service()),
    api_key: str = Security(verify_api_key),
) -> Dict:
    """Returns { url: [link to checkout session] }"""

    return await payment_service.create_checkout_session(data.user_id)


@router.get("/portal/{user_id}")
async def get_portal_link(
    user_id: str,
    request: Request,
    payment_service: PaymentService = Depends(lambda: container.get_payment_service()),
    api_key: str = Security(verify_api_key),
) -> Dict:
    """Returns { url: [portal link] }"""

    return await payment_service.get_portal_link(user_id)
