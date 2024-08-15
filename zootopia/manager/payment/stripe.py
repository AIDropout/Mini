from abc import ABC
from config.config import config
import stripe


class StripeBaseClient(ABC):
    """Base class for all Stripe-related operations."""

    def init(self):
        """Initializes the client with the Stripe API key."""
        if not config.STRIPE_SECRET_KEY_TEST:
            raise ValueError("The Stripe API key must be set.")
        stripe.api_key = config.STRIPE_SECRET_KEY_TEST
