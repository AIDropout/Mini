import stripe
from typing import Any, Dict
from .stripe import StripeBaseClient
from zootopia.manager.database import DatabaseManager
from config.config import config
from zootopia.core.logger import get_logger
from typing import Optional

logger = get_logger(__name__)


class CheckoutManager(StripeBaseClient):
    """Manages checkout session."""

    def __init__(self):
        """Initializes the client with the Stripe API key."""
        super().__init__()

    def create_checkout_session(
        self,
        user_id: str,
        email: str,
        frequency: str,
        customer_id: Optional[str] = None,
        trial=True,
    ) -> stripe.checkout.Session:
        """Creates a checkout session for a given user and price."""

        price_id = config.STRIPE_WEEKLY_PRICE_ID

        # if frequency.lower() == 'yearly':
        #     price_id = STRIPE_YEARLY_PRICE_ID

        session_params = {
            "line_items": [
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            "subscription_data": {},
            "mode": "subscription",
            "metadata": {"user_id": user_id},
            "success_url": "http://boyfriend.so/?success=true",
        }

        # Use customer_id if it's provided, otherwise use customer_email
        if customer_id:
            session_params["customer"] = customer_id
        else:
            session_params["customer_email"] = email

        # if email.endswith('.edu'):
        #     session_params['discounts'] = [{
        #         'coupon': STRIPE_EDU_COUPON_ID
        #     }]
        # else:
        #     session_params['allow_promotion_codes'] = True

        session = stripe.checkout.Session.create(**session_params)
        return session


if __name__ == "__main__":
    # from database import DatabaseManager
    # db_manager = DatabaseManager()
    # checkout_manager = CheckoutManager(db_manager)
    checkout_manager = CheckoutManager()
    session = checkout_manager.create_checkout_session("urmom", "monthly")
    print(session)
