import stripe

from config.config import config
from mini.core.logger import get_logger

from .stripe import StripeBaseClient

logger = get_logger(__name__)


class CheckoutManager(StripeBaseClient):
    """Manages checkout session."""

    def __init__(self):
        """Initializes the client with the Stripe API key."""
        super().__init__()

    def create_checkout_session(
        self,
        user_id: str,
        phone: str,
        customer_id: str,
    ) -> stripe.checkout.Session:
        """Creates a checkout session for a given user and price.

        Session Object: https://docs.stripe.com/api/checkout/sessions/object
        """

        price_id = config.STRIPE_PRODUCT_PRICE_ID

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
            "success_url": f"{config.FRONTEND_URL}/subscription-success",
            "allow_promotion_codes": True,
        }

        session_params["customer"] = customer_id

        # session_params['allow_promotion_codes'] = True

        session = stripe.checkout.Session.create(**session_params)
        return session


if __name__ == "__main__":
    checkout_manager = CheckoutManager()
    session = checkout_manager.create_checkout_session(1)
    print(session)
