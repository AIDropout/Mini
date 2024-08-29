from typing import Optional

from config.config import config
from zootopia.core.rate_limiter import RateLimiter
from zootopia.manager.database import DatabaseManager
from zootopia.manager.llm import LLMManager
from zootopia.manager.memory import MemoryManager
from zootopia.manager.messaging import MessagingManagerFactory
from zootopia.manager.payment import (
    CheckoutManager,
    CustomerManager,
    SubscriptionManager,
)
from zootopia.manager.time import TimeManager
from zootopia.server.redis import RedisManager
from zootopia.service.context_factory import ContextFactory
from zootopia.service.user_service import UserService


class Container:
    def __init__(self):
        self.database_manager = DatabaseManager()
        self.time_manager: TimeManager = TimeManager(
            # TODO: Save user's timezone on signup
            user_timezone=config.TIME_API.default_timezone
        )
        self.messaging_manager_factory: Optional[MessagingManagerFactory] = None
        self.checkout_manager = CheckoutManager()
        self.customer_manager = CustomerManager.from_config(config)
        self.subscription_manager = SubscriptionManager()
        self.user_service: Optional[UserService] = None
        self._context_factory: Optional[ContextFactory] = None
        self.redis_manager: Optional[RedisManager] = None
        self.rate_limiter: Optional[RateLimiter] = None
        self.memory_manager: Optional[MemoryManager] = None

    def get_rate_limiter(self):
        if self.rate_limiter is None:
            self.rate_limiter = RateLimiter(
                redis_manager=self.get_redis_manager(), max_calls=5, period=300
            )

        return self.rate_limiter

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

    def get_memory_manager(self):
        if self.memory_manager is None:

            def lazy_init_llm():
                return LLMManager(
                    llm_name=config.MEMORY_GENERAL_LLM,
                    llm_provider=config.MEMORY_GENERAL_LLM_PROVIDER,
                )

            self.memory_manager = MemoryManager(
                user_id=None,
                agent_id=None,
                time_manager=self.time_manager,
                llm_manager=lazy_init_llm(),
                memory_save_delay=5,
            )

        return self.memory_manager

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
        from zootopia.service.room_service import RoomService

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

    def get_agent_controller(self):
        from zootopia.controller.agent.agent import AgentService
        from zootopia.controller.agent.modules.action import ActionModule
        from zootopia.controller.agent.modules.intent.filter import FilterModule
        from zootopia.controller.agent.modules.intent.intent import (
            Confidence,
            IntentConfig,
        )
        from zootopia.controller.agent.modules.memory import MemoryModule
        from zootopia.controller.agent.modules.subscribe import SubscribeModule
        from zootopia.controller.agent.modules.vision import VisionModule

        action_module = ActionModule(
            llm_manager=LLMManager(
                llm_name=config.ACTION_MANAGER_LLM,
                llm_provider=config.ACTION_MANAGER_LLM_PROVIDER,
            )
        )

        memory_manager = self.get_memory_manager()
        memory_llm_manager = memory_manager.llm_manager
        memory_module = MemoryModule(
            database_manager=self.database_manager,
            memory_manager=memory_manager,
            llm_manager=memory_llm_manager,
        )
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

        # TODO: temp using openai creds in a weird way, much change!!
        vision_llm_man = LLMManager(
            llm_name=config.VISION_MANAGER_LLM,
            llm_provider=config.VISION_MANAGER_LLM_PROVIDER,
        )
        vision_llm_man.api_key = config.MEMORY_EMBEDDINGS_CONFIG.api_key
        vision_module = VisionModule(
            database_manager=self.database_manager,
            llm_manager=vision_llm_man,
        )

        return AgentService(
            database_manager=self.database_manager,
            action_module=action_module,
            memory_module=memory_module,
            subscribe_module=subscribe_module,
            filter_module=filter_module,
            vision_module=vision_module,
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
