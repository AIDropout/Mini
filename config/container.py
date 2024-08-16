from zootopia.manager.database import DatabaseManager
from zootopia.manager.messaging import MessagingManagerFactory, BirdManager
from zootopia.service.context import ContextFactory
from zootopia.service.reply_service import ReplyService
from zootopia.service.cron_service import CronService
from zootopia.service.signup_service import SignupService
from zootopia.service.sms_otp_service import SMSOTPService
from zootopia.manager.payment import (
    CheckoutManager,
    CustomerManager,
    SubscriptionManager,
)
from zootopia.service.payment_service import PaymentService
from zootopia.service.dashboard_service import DashboardService


class Container:
    def __init__(self):
        self.database_manager = DatabaseManager()
        self.messaging_manager_factory = MessagingManagerFactory()
        self.context_factory = ContextFactory(
            messaging_manager_factory=self.messaging_manager_factory
        )

        self.reply_service = ReplyService(
            database_manager=self.database_manager,
            context_factory=self.context_factory,
            messaging_manager_factory=self.messaging_manager_factory,
        )

        self.cron_service = CronService(
            database_manager=self.database_manager,
            messaging_manager=self.messaging_manager_factory.bird_manager,
        )

        self.signup_service = SignupService(
            database_manager=self.database_manager,
            messaging_manager=self.messaging_manager_factory.bird_manager,
        )

        self.sms_otp_service = SMSOTPService(
            bird_manager=self.messaging_manager_factory.bird_manager
        )

        self.checkout_manager = CheckoutManager()
        self.customer_manager = CustomerManager()
        self.subscription_manager = SubscriptionManager()

        self.payment_service = PaymentService(
            database_manager=self.database_manager,
            checkout_manager=self.checkout_manager,
            customer_manager=self.customer_manager,
            subscription_manager=self.subscription_manager,
        )

        self.dashboard_service = DashboardService(
            database_manager=self.database_manager,
            context_factory=self.context_factory,
            messaging_manager_factory=self.messaging_manager_factory,
        )


# Create a global instance of the container
container = Container()
