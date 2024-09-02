from datetime import datetime

import stripe
from fastapi import HTTPException

from config.config import config
from mini.core.logger import get_logger
from mini.core.schema.tables import Subscription, Tables, User
from mini.manager.database import DatabaseManager
from mini.manager.payment import CheckoutManager, CustomerManager, SubscriptionManager

from .base import Service

logger = get_logger(__name__)


class PaymentService(Service):
    def __init__(
        self,
        database_manager: DatabaseManager,
        checkout_manager: CheckoutManager,
        customer_manager: CustomerManager,
        subscription_manager: SubscriptionManager,
    ):
        super().__init__(database_manager)
        self._checkout_manager = checkout_manager
        self._customer_manager = customer_manager
        self._subscription_manager = subscription_manager

    async def create_checkout_session(self, user_id: str):
        user = self.database_manager.get_row(
            Tables.USERS,
            {Tables.USERS__id: user_id},
        )

        if not user:
            raise HTTPException(
                status_code=404, detail=f"User with id {user_id} not found"
            )

        phone_number = user.phone_number
        customer_id = user.customer_id

        response = self._checkout_manager.create_checkout_session(
            user_id,
            phone_number,
            customer_id,
        )

        return {"url": response.url}

    async def get_portal_link(self, user_id: str):
        user = self.database_manager.get_row(
            Tables.USERS,
            {Tables.USERS__id: user_id},
        )
        customer_id = user.customer_id
        response = self._customer_manager.get_portal_link(customer_id)
        return {"url": response.url}

    async def process_event(self, event_payload: str, sig_header: str) -> None:
        """Processes the event received from Stripe webhook."""
        if not config.STRIPE_WEBHOOK_SECRET:
            raise ValueError("The Stripe webhook secret must be set.")

        try:
            event = stripe.Webhook.construct_event(
                payload=event_payload,
                sig_header=sig_header,
                secret=config.STRIPE_WEBHOOK_SECRET,
            )
            await self._handle_event(event)

        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            return event.type, None
        except Exception as e:
            logger.error(f"An error occurred while processing the webhook event: {e}")
            return event.type, None

    async def _handle_event(self, event: stripe.Event) -> None:
        """Handles the event with the given Stripe event object."""
        if event.type == "checkout.session.completed":
            logger.info(f"Received event: {event.type}")
            return await self._handle_checkout_session_completed(event.data.object)
        elif event.type == "customer.subscription.deleted":
            logger.info(f"Received event: {event.type}")
            return await self._handle_subscription_deleted(event.data.object)
        else:
            logger.warning(f"Not handling {event.type}")

    async def _handle_checkout_session_completed(
        self, session: stripe.checkout.Session
    ) -> None:
        """Handles the checkout.subscription.completed event."""
        logger.debug(f"Handling checkout.session.completed event")
        subscription_id = session.subscription
        user_id = session.metadata.get("user_id", None)

        try:
            subscription = self._subscription_manager.retrieve_subscription(
                subscription_id
            )

            self.database_manager.insert(
                table_name=Tables.SUBSCRIPTIONS,
                item=Subscription(
                    id=subscription.id,
                    user_id=user_id,
                    status=subscription.status,
                ),
            )

            self.database_manager.update(
                Tables.USERS,
                {Tables.USERS__is_subscribed: True},
                condition_key=Tables.USERS__id,
                condition_value=user_id,
            )
        except Exception as e:
            logger.error(f"Error retrieving subscription information: {e}")
            raise e

    async def _handle_subscription_deleted(
        self, subscription: stripe.Subscription
    ) -> None:
        """Handles the customer.subscription.deleted event."""
        logger.debug(f"Handling customer.subscription.deleted event")
        try:
            # user_id = subscription.metadata.get("user_id", None)
            updated_subscription = self.database_manager.update(
                table_name=Tables.SUBSCRIPTIONS,
                update_data={Tables.SUBSCRIPTIONS__status: subscription.status},
                condition_key=Tables.SUBSCRIPTIONS__id,
                condition_value=subscription.id,
            )

            self.database_manager.update(
                table_name=Tables.USERS,
                update_data={Tables.USERS__is_subscribed: False},
                condition_key=Tables.USERS__id,
                condition_value=updated_subscription.user_id,
            )
        except Exception as e:
            logger.error(f"Error retrieving subscription information: {e}")
            raise e
