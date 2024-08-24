from typing import Optional

from config.config import config
from zootopia.manager.database import DatabaseManager
from zootopia.manager.llm import LLMManager
from zootopia.manager.messaging import MessagingManagerFactory
from zootopia.manager.payment import (
    CheckoutManager,
    CustomerManager,
    SubscriptionManager,
)
from zootopia.server.redis import RedisManager
from zootopia.service.context_factory import ContextFactory
from zootopia.service.user_service import UserService


class Container:
    def __init__(self):
        self.database_manager = DatabaseManager()
        self.messaging_manager_factory: Optional[MessagingManagerFactory] = None
        self.checkout_manager = CheckoutManager()
        self.customer_manager = CustomerManager.from_config(config)
        self.subscription_manager = SubscriptionManager()
        self.user_service: Optional[UserService] = None
        self._context_factory: Optional[ContextFactory] = None
        self.redis_manager: Optional[RedisManager] = None

    def get_redis_manager(self):
        if self.redis_manager is None:
            self.redis_manager = RedisManager()

        return self.redis_manager

    def get_messaging_manager_factory(self):
        from zootopia.manager.messaging import MessagingManagerFactory

        if self.messaging_manager_factory is None:
            self.messaging_manager_factory = MessagingManagerFactory()

        return self.messaging_manager_factory

    def get_user_service(self):
        from zootopia.service.user_service import UserService

        if self.user_service is None:
            self.user_service = UserService(
                database_manager=self.database_manager,
                customer_manager=self.customer_manager,
            )
        return self.user_service

    def get_agent_service(self):
        from zootopia.service.agent_service import AgentService

        return AgentService(database_manager=self.database_manager)

    def get_context_factory(self) -> ContextFactory:
        if self._context_factory is None:
            self._context_factory = ContextFactory(
                database_manager=self.database_manager,
                user_service=self.get_user_service(),
            )
        return self._context_factory

    def get_cron_service(self):
        from zootopia.service.cron_service import CronService

        return CronService(
            database_manager=self.database_manager,
            messaging_manager=self.get_messaging_manager_factory().bird_manager,
        )

    def get_sms_otp_service(self):
        from zootopia.service.sms_otp_service import SMSOTPService

        return SMSOTPService(
            bird_manager=self.get_messaging_manager_factory().bird_manager
        )

    def get_room_service(self):
        from zootopia.service._room_service import RoomService

        return RoomService(
            database_manager=self.database_manager,
            messaging_manager=self.get_messaging_manager_factory().bird_manager,
            customer_manager=self.customer_manager,
            user_service=self.get_user_service(),
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
            messaging_manager_factory=self.get_messaging_manager_factory(),
            context_factory=self.get_context_factory(),
        )

    def get_scheduler_service(self):
        from zootopia.controller.task.task_scheduler import SchedulerService

        return SchedulerService(
            database_manager=self.database_manager,
            redis_manager=self.get_redis_manager(),
        )

    def get_agent_service(self):
        from zootopia.controller.agent.agent import AgentService
        from zootopia.controller.agent.modules.action import ActionModule
        from zootopia.controller.agent.modules.intent.filter import FilterModule
        from zootopia.controller.agent.modules.intent.intent import (
            Confidence,
            IntentConfig,
        )
        from zootopia.controller.agent.modules.memory import MemoryModule
        from zootopia.controller.agent.modules.subscribe import SubscribeModule

        action_module = ActionModule(
            llm_manager=LLMManager(
                llm_name=config.ACTION_MANAGER_LLM,
                llm_provider=config.ACTION_MANAGER_LLM_PROVIDER,
            )
        )
        memory_module = MemoryModule(database_manager=self.database_manager)
        subscribe_module = SubscribeModule(
            database_manager=self.database_manager,
            action_module=action_module,
            memory_module=memory_module,
        )

        filter_module = FilterModule.from_config(
            IntentConfig(
                message_input_count=5,
                confidence_threshold=Confidence.HIGH,
                enabled=True,
            ),
            llm_manager=LLMManager(
                llm_name=config.ACTION_MANAGER_LLM,
                llm_provider=config.ACTION_MANAGER_LLM_PROVIDER,  # Configure a Filter LLM
            ),
        )

        return AgentService(
            database_manager=self.database_manager,
            action_module=action_module,
            memory_module=memory_module,
            subscribe_module=subscribe_module,
            filter_module=filter_module,
        )

    def get_reply_service(self):
        from zootopia.service.reply_service import ReplyService

        return ReplyService(
            database_manager=self.database_manager,
            messaging_manager_factory=self.get_messaging_manager_factory(),
            context_factory=self.get_context_factory(),
            scheduler_service=self.get_scheduler_service(),
        )


container = Container()  # Global instance of the container
