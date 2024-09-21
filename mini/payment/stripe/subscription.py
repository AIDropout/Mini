from typing import Any, Dict, List

import stripe

from .stripe import StripeBaseClient


class SubscriptionManager(StripeBaseClient):
    """Manages subscription operations in Stripe."""

    def __init__(self):
        """Initializes the client with the Stripe API key."""
        super().__init__()

    def create_subscription(
        self, customer_id: str, price_id: str, trial_period_days: int = None
    ) -> Dict[str, Any]:
        """Creates a subscription for a customer."""
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            trial_period_days=trial_period_days,
        )
        return subscription

    def retrieve_subscription(self, subscription_id: str) -> stripe.Subscription:
        """Retrieves a subscription's details."""
        subscription = stripe.Subscription.retrieve(subscription_id)
        return subscription

    def update_subscription(
        self, subscription_id: str, update_params: Dict, price_id: str = None
    ) -> Dict[str, Any]:
        """Updates a subscription's details."""
        if price_id:
            update_params["items"] = [{"price": price_id}]
        subscription = stripe.Subscription.modify(subscription_id, **update_params)
        return subscription

    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Cancels a subscription at the end of the current billing period."""
        subscription = stripe.Subscription.modify(
            subscription_id, cancel_at_period_end=True
        )
        return subscription

    def resume_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Resumes a subscription."""
        subscription = stripe.Subscription.modify(
            subscription_id, cancel_at_period_end=False
        )
        return subscription

    def list_subscriptions(self, customer_id: str) -> List[Dict[str, Any]]:
        """Lists all subscriptions for a customer."""
        subscriptions = stripe.Subscription.list(customer=customer_id)
        return subscriptions["data"]
