from .stripe import StripeBaseClient
from typing import Dict, Any
import stripe


class CustomerManager(StripeBaseClient):
    """Manages customer operations in Stripe."""

    def __init__(self):
        super().__init__()

    def create_customer(self, email: str, **kwargs) -> stripe.Customer:
        """Creates a new customer in Stripe."""
        return stripe.Customer.create(email=email, **kwargs)

    def list_customers(self, **kwargs) -> stripe.Customer:
        """Lists all customers in Stripe."""
        return stripe.Customer.list(**kwargs)

    def get_customer_by_email(self, email: str) -> stripe.Customer:
        """Retrieves a customer by email."""
        customers = stripe.Customer.list(email=email)
        if len(customers.data) > 0:
            return customers.data[0]

    def retrieve_customer(self, customer_id: str) -> stripe.Customer:
        """Retrieves a customer's information."""
        customer = stripe.Customer.retrieve(customer_id)
        if customer.deleted:
            return None
        return customer

    def update_customer(self, customer_id: str, **kwargs) -> Dict[str, Any]:
        """Updates a customer's information."""
        customer = stripe.Customer.retrieve(customer_id)
        return customer.modify(customer_id, **kwargs)

    def delete_customer(self, customer_id: str) -> Dict[str, Any]:
        """Deletes a customer."""
        customer = stripe.Customer.retrieve(customer_id)
        return customer.delete()

    def get_payment_method(self, customer_id: str) -> Dict[str, Any]:
        """Retrieves the default payment method for a given customer."""
        customer = stripe.Customer.retrieve(customer_id)
        if customer.invoice_settings.default_payment_method:
            payment_method = stripe.PaymentMethod.retrieve(
                customer.invoice_settings.default_payment_method
            )
            return payment_method

    def get_portal_link(self, customer_id: str) -> stripe.billing_portal.Session:
        """Retrieves the link to the Stripe customer portal."""
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url="https://app.youlearn.ai"
        )
        return session

    def get_customer_subscriptions(self, customer_id: str) -> stripe.Subscription:
        """Retrieves a customer's subscriptions."""
        subscriptions = stripe.Subscription.list(customer=customer_id)
        return subscriptions


if __name__ == '__main__':
    customer_manager = CustomerManager()
    customer = customer_manager.get_portal_link("cus_P2mvWPPveMDq1g")
    print(customer)
