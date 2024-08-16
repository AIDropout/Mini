# TODO: WIP

from .base import Service
from zootopia.manager.stripe import (
    CheckoutManager,
    CustomerManager,
    SubscriptionManager,
)
from zootopia.manager.database import DatabaseManager
from zootopia.core.schema.tables import Tables
from typing import Literal, Optional, Dict, Any, Tuple
from config.config import config
import stripe
from datetime import datetime
from zootopia.core.schema import User
from zootopia.core.logger import get_logger

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
            Tables.USERS.value,
            {Tables.USERS__id.value: user_id},
        )
        phone_number = user.phone_number
        customer_id = user.customer_id

        response = self._checkout_manager.create_checkout_session(
            user_id, phone_number, customer_id
        )

        return {"url": response.url}

    async def get_portal_link(self, user_id: str):
        user = self.database_manager.get_row(
            Tables.USERS.value,
            {Tables.USERS__id.value: user_id},
        )
        customer_id = user.customer_id
        response = self._customer_manager.get_portal_link(customer_id)
        return {"url": response.url}

    async def process_event(
        self, event_payload: str, sig_header: str
    ) -> None:
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

            # customer = await self.database_manager.update(
            #     user_id=user_id,
            #     customer_id=subscription.customer,
            #     subscription_status=subscription.status,
            #     subscription_id=subscription.id,
            # )

            updated_customer = self.database_manager.update(
                table_name=Tables.USERS.value,
                item=User(
                    stripe_customer_id=subscription.customer,
                    subscription_status=subscription.status,
                    subscription_id=subscription.id,
                ),
                condition_key=Tables.USERS__id.value,
                condition_value=user_id,
            )
        except Exception as e:
            logger.error(f"Error retrieving subscription information: {e}")
            raise e

    async def _handle_subscription_deleted(
        self, subscription: stripe.Subscription
    ) -> None:
        """Handles the customer.subscription.deleted event."""
        pass
        # logger.debug(f"Handling customer.subscription.deleted event")
        # try:
        #     user_id = subscription.metadata.get("user_id", None)
        #     subscription_data = Subscription(
        #         id=subscription.id,
        #         status=subscription.status,
        #         created_at=datetime.fromtimestamp(subscription.created),
        #         tier="free",
        #     )
        #     customer = await self.database_manager.update_user_customer_subscription(
        #         user_id=user_id,
        #         customer_id=subscription.customer,
        #         subscription_data=subscription_data,
        #     )
        # except Exception as e:
        #     logger.error(f"Error retrieving subscription information: {e}")
        #     raise e
