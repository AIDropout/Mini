from abc import ABC

import stripe

from config.config import config


class StripeBaseClient(ABC):
    """Base class for all Stripe-related operations."""

    def __init__(self):
        """Initializes the client with the Stripe API key."""
        if not config.STRIPE_SECRET_KEY:
            raise ValueError("The Stripe API key must be set.")
        stripe.api_key = config.STRIPE_SECRET_KEY
