# # TODO: WIP

# from fastapi import APIRouter, Request, Depends, BackgroundTasks
# from models.user_models import UserId
# from pydantic import BaseModel, Field
# from zootopia.service.payment_service import PaymentService
# from config.container import container
# from models.events import EventType
# from typing import Dict

# router = APIRouter(
#     prefix="/payment",
#     tags=["payment"],
# )


# def get_payment_service() -> PaymentService:
#     return container.payment_service


# @router.post("/webhook")
# async def stripe_webhook(
#     request: Request,
#     background_tasks: BackgroundTasks,
#     payment_service: PaymentService = Depends(get_payment_service),
# ) -> bool:
#     payload = await request.body()
#     sig_header = request.headers.get("stripe-signature")
#     event_type, customer = await payment_service.process_event(payload, sig_header)
#     if event_type == "checkout.session.completed" and customer:
#         data = {
#             "email": customer.user.email,
#         }
#         background_tasks.add_task(
#             EVENT_MANAGER.post_event,
#             EventType.CHECKOUT_SESSION_COMPLETED,
#             data,
#             request,
#         )
#     return True


# class Checkout(BaseModel):
#     user_id: str = Field(..., description="Unique identifier of the user.")
#     frequency: str = Field(
#         ..., description="Frequency to subscribe to.", examples=["monthly", "yearly"]
#     )


# @router.post("/checkout")
# async def create_checkout_session(
#     data: Checkout,
#     request: Request,
#     background_tasks: BackgroundTasks,
#     payment_service: PaymentService = Depends(get_payment_service),
#     verify: bool = Depends(USER_AUTHENTICATOR.post_verify_session_cookie),
# ) -> Dict:
#     response = await payment_service.create_checkout_session(
#         data.user_id, data.frequency
#     )

#     background_tasks.add_task(
#         EVENT_MANAGER.post_event, EventType.PAYMENT_CHECKOUT, data, request
#     )
#     return response


# @router.get("/portal/{user_id}")
# async def get_portal_link(
#     user_id: str,
#     request: Request,
#     background_tasks: BackgroundTasks,
#     payment_service: PaymentService = Depends(get_payment_service),
#     verify: bool = Depends(USER_AUTHENTICATOR.get_verify_session_cookie),
# ) -> Dict:
#     response = await payment_service.get_portal_link(user_id)
#     background_tasks.add_task(
#         EVENT_MANAGER.post_event,
#         EventType.PAYMENT_PORTAL,
#         # UserId(user_id=user_id),
#         request,
#     )
#     return response
