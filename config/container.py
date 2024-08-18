# container.py
from zootopia.manager.database import DatabaseManager
from zootopia.manager.messaging import MessagingManagerFactory
from zootopia.manager.llm import LLMManager
from zootopia.manager.payment import (
    CheckoutManager,
    CustomerManager,
    SubscriptionManager,
)
from zootopia.service.context_factory import ContextFactory
from config.config import config


class Container:
    def __init__(self):
        self.database_manager = DatabaseManager()
        self.messaging_manager_factory = MessagingManagerFactory()
        self.checkout_manager = CheckoutManager()
        self.customer_manager = CustomerManager.from_config(config)
        self.subscription_manager = SubscriptionManager()
        self.context_factory = ContextFactory(database_manager=self.database_manager)

    def get_cron_service(self):
        from zootopia.service.cron_service import CronService

        return CronService(
            database_manager=self.database_manager,
            messaging_manager=self.messaging_manager_factory.bird_manager,
        )

    def get_sms_otp_service(self):
        from zootopia.service.sms_otp_service import SMSOTPService

        return SMSOTPService(bird_manager=self.messaging_manager_factory.bird_manager)

    def get_signup_service(self):
        from zootopia.service.signup_service import SignupService

        return SignupService(
            database_manager=self.database_manager,
            messaging_manager=self.messaging_manager_factory.bird_manager,
            customer_manager=self.customer_manager,
        )

    def get_payment_service(self):
        from zootopia.service.payment_service import PaymentService

        return PaymentService(
            database_manager=self.database_manager,
            checkout_manager=self.checkout_manager,
            customer_manager=self.customer_manager,
            subscription_manager=self.subscription_manager,
        )

    def get_dashboard_service(self):
        from zootopia.service.dashboard_service import DashboardService

        return DashboardService(
            database_manager=self.database_manager,
            messaging_manager_factory=self.messaging_manager_factory,
            context_factory=self.context_factory,
        )

    def get_scheduler_service(self):
        from zootopia.controller.task.task_scheduler import SchedulerService

        return SchedulerService(
            database_manager=self.database_manager,
        )

    def get_agent_service(self):
        from zootopia.controller.agent.agent import AgentService
        from zootopia.controller.agent.modules.subscribe import SubscribeModule
        from zootopia.controller.agent.modules.action import ActionModule
        from zootopia.controller.agent.modules.memory import MemoryModule

        action_module = ActionModule(llm_manager=LLMManager(config.ACTION_MANAGER_LLM))
        memory_module = MemoryModule(database_manager=self.database_manager)
        subscribe_module = SubscribeModule(
            database_manager=self.database_manager,
            action_module=action_module,
            memory_module=memory_module,
        )

        return AgentService(
            database_manager=self.database_manager,
            action_module=action_module,
            memory_module=memory_module,
            subscribe_module=subscribe_module,
        )

    def get_reply_service(self):
        from zootopia.service.reply_service import ReplyService

        return ReplyService(
            database_manager=self.database_manager,
            messaging_manager_factory=self.messaging_manager_factory,
            context_factory=self.context_factory,
            scheduler_service=self.get_scheduler_service(),
        )


# Create a global instance of the container
container = Container()
