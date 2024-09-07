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

    @staticmethod
    def get_price_id(tier: str):
        if tier == "basic":
            return config.STRIPE_CONFIG.basic_weekly_price_id
        elif tier == "pro":
            return config.STRIPE_CONFIG.pro_weekly_price_id
        return None

    def create_checkout_session(
        self,
        user_id: str,
        phone: str,
        customer_id: str,
        tier: str
    ) -> stripe.checkout.Session:
        """Creates a checkout session for a given user and price.

        Session Object: https://docs.stripe.com/api/checkout/sessions/object
        """

        price_id = self.get_price_id(tier)

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

        session = stripe.checkout.Session.create(**session_params)
        return session


if __name__ == "__main__":
    checkout_manager = CheckoutManager()
    session = checkout_manager.create_checkout_session(1)
    print(session)
