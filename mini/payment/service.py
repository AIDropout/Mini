import stripe

from config.config import config
from mini.core.logger import get_logger
from mini.database.models import Tables
from mini.database.tables.subscriptions_service import SubscriptionTableService
from mini.database.tables.user_service import UserTableService
from mini.payment.stripe import CheckoutManager, CustomerManager, SubscriptionManager
from mini.messaging.providers.discord import discord_manager


logger = get_logger(__name__)


class PaymentService:
    def __init__(
        self,
        checkout_manager: CheckoutManager,
        customer_manager: CustomerManager,
        subscription_manager: SubscriptionManager,
        subscription_table_service: SubscriptionTableService,
        user_table_service: UserTableService,
    ):
        self._checkout_manager = checkout_manager
        self._customer_manager = customer_manager
        self._subscription_manager = subscription_manager
        self.subscription_table_service = subscription_table_service
        self.user_table_service = user_table_service

    def create_checkout_session(self, user_id: str, tier: str):
        user = self.user_table_service.get_user(user_id)
        phone_number = user.phone_number
        customer_id = user.customer_id
        response = self._checkout_manager.create_checkout_session(
            user_id,
            phone_number,
            customer_id,
            tier,
        )

        return {"url": response.url}

    def get_portal_link(self, user_id: str):
        user = self.user_table_service.get_user(user_id)
        customer_id = user.customer_id
        response = self._customer_manager.get_portal_link(customer_id)
        return {"url": response.url}

    def process_event(self, event_payload: str, sig_header: str) -> None:
        """Processes the event received from Stripe webhook."""
        if not config.STRIPE_CONFIG.webhook_secret:
            raise ValueError("The Stripe webhook secret must be set.")

        try:
            event = stripe.Webhook.construct_event(
                payload=event_payload,
                sig_header=sig_header,
                secret=config.STRIPE_CONFIG.webhook_secret,
            )
            self._handle_event(event)

        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            return event.type, None
        except Exception as e:
            logger.error(f"An error occurred while processing the webhook event: {e}")
            return event.type, None

    def _handle_event(self, event: stripe.Event) -> None:
        """Handles the event with the given Stripe event object."""
        if event.type == "checkout.session.completed":
            logger.info(f"Received event: {event.type}")
            return self._handle_checkout_session_completed(event.data.object)
        elif event.type == "customer.subscription.deleted":
            logger.info(f"Received event: {event.type}")
            return self._handle_subscription_deleted(event.data.object)
        else:
            logger.warning(f"Not handling {event.type}")

    def _handle_checkout_session_completed(
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

            self.subscription_table_service.add_subscription(
                subscription.id, user_id, subscription.status
            )

            self.user_table_service.update_user(
                user_id=user_id,
                update_data={Tables.USERS__is_subscribed: True},
            )

            if config.ENVIRONMENT == "production":
                discord_manager.log_website_activity(
                    message=f"-# **Subscription created** 🎉: user {user_id}",
                )

        except Exception as e:
            logger.error(f"Error retrieving subscription information: {e}")
            raise e

    def _handle_subscription_deleted(self, subscription: stripe.Subscription) -> None:
        """Handles the customer.subscription.deleted event."""
        logger.debug(f"Handling customer.subscription.deleted event")
        try:
            # user_id = subscription.metadata.get("user_id", None)

            updated_subscription = (
                self.subscription_table_service.update_subscription_status(
                    subscription.id, subscription.status
                )
            )

            self.user_table_service.update_user(
                user_id=updated_subscription.user_id,
                update_data={Tables.USERS__is_subscribed: False},
            )

        except Exception as e:
            logger.error(f"Error retrieving subscription information: {e}")
            raise e
