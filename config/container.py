from typing import Optional

from config.config import config
from mini.agent.modules.memory import MemoryManager
from mini.core.logger import get_logger
from mini.core.rate_limiter import RateLimiter
from mini.database.database import DatabaseManager
from mini.database.users.service import UserService
from mini.llm import LLMService, Model
from mini.messaging.bird.bird import BirdMessagingService
from mini.messaging.context import ContextFactory
from mini.messaging.instagram.instagram import InstagramMessagingService
from mini.payment.stripe import CheckoutManager, CustomerManager, SubscriptionManager
from mini.server.cancel import CancelManager
from mini.server.redis import RedisManager
from mini.server.schedule import TaskScheduler
from mini.utils.time import TimeManager

logger = get_logger(__name__)


class Container:
    def __init__(self):
        self.database_manager = DatabaseManager()
        self.time_manager: TimeManager = TimeManager(
            # TODO: Save user's timezone on signup
            user_timezone=config.TIME_API.default_timezone
        )
        self.checkout_manager = CheckoutManager()
        self.customer_manager = CustomerManager.from_config(config)
        self.subscription_manager = SubscriptionManager()
        self.user_service: Optional[UserService] = None
        self._context_factory: Optional[ContextFactory] = None
        self.redis_manager: Optional[RedisManager] = None
        self.rate_limiter: Optional[RateLimiter] = None
        self.memory_manager: Optional[MemoryManager] = None
        self.cancel_manager: Optional[CancelManager] = None

    def get_cancel_manager(self):
        if self.cancel_manager is None:
            self.cancel_manager = CancelManager(redis_manager=self.get_redis_manager())
        return self.cancel_manager

    def get_rate_limiter(self):
        if self.rate_limiter is None:
            self.rate_limiter = RateLimiter(
                redis_manager=self.get_redis_manager(), max_calls=20, period=300
            )

        return self.rate_limiter

    def get_redis_manager(self):
        if self.redis_manager is None:
            self.redis_manager = RedisManager()

        return self.redis_manager

    def get_user_service(self):
        from mini.database.users.service import UserService

        if self.user_service is None:
            self.user_service = UserService(
                database_manager=self.database_manager,
                customer_manager=self.customer_manager,
            )
        return self.user_service

    def get_agent_service(self):
        from mini.database.agents.service import AgentService

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
                return LLMService(
                    model=Model.from_model_name(config.MEMORY_GENERAL_LLM),
                )

            self.memory_manager = MemoryManager(
                user_id=None,
                agent_id=None,
                time_manager=self.time_manager,
                llm_manager=lazy_init_llm(),
                memory_save_delay=5,
            )

        return self.memory_manager

    def get_verify_service(self):
        from mini.messaging.bird.bird import BirdMessagingService
        from mini.messaging.bird.verification.service import VerifyService

        return VerifyService(bird_manager=BirdMessagingService())

    def get_room_service(self):
        from mini.database.rooms.service import RoomService

        return RoomService(
            database_manager=self.database_manager,
            customer_manager=self.customer_manager,
            user_service=self.get_user_service(),
        )

    def get_payment_service(self):
        from mini.payment.service import PaymentService

        return PaymentService(
            database_manager=self.database_manager,
            checkout_manager=self.checkout_manager,
            customer_manager=self.customer_manager,
            subscription_manager=self.subscription_manager,
        )

    def get_dashboard_service(self):
        from mini.dashboard.service import DashboardService

        return DashboardService(
            database_manager=self.database_manager,
            context_factory=self.get_context_factory(),
        )

    def get_agent_controller(self):
        from mini.agent.agent import AgentService
        from mini.agent.modules.action import ActionModule
        from mini.agent.modules.filter.filter import IntentConfig, MessageFilterModule
        from mini.agent.modules.memory.service import MemoryModule
        from mini.agent.modules.prompt import BasePromptModule
        from mini.agent.modules.subscribe import SubscribeModule
        from mini.agent.modules.vision import VisionModule
        from mini.core.enums import ConfidenceLevel

        action_module = ActionModule(
            llm_manager=LLMService(
                model=Model.from_model_name(config.ACTION_MANAGER_LLM)
            )
        )

        memory_manager = self.get_memory_manager()
        memory_module = MemoryModule(
            database_manager=self.database_manager,
            memory_manager=memory_manager,
        )
        subscribe_module = SubscribeModule(
            database_manager=self.database_manager,
            action_module=action_module,
            memory_module=memory_module,
        )

        filter_module = MessageFilterModule.from_config(
            IntentConfig(
                message_input_count=5,
                confidence_threshold=ConfidenceLevel.HIGH,
                is_enabled=True,
            ),
            llm_service=LLMService(
                model=Model.from_model_name(config.ACTION_MANAGER_LLM)
            ),
        )

        # TODO: temp using openai creds in a weird way, much change!!
        vision_llm_man = LLMService(
            model=Model.from_model_name(config.VISION_MANAGER_LLM)
        )
        vision_llm_man.api_key = config.MEMORY_EMBEDDINGS_CONFIG.api_key
        vision_module = VisionModule(
            database_manager=self.database_manager,
            llm_manager=vision_llm_man,
        )

        prompt_module = BasePromptModule(
            database_manager=self.database_manager,
            time_manager=self.time_manager,
        )

        return AgentService(
            database_manager=self.database_manager,
            task_scheduler=self.get_task_scheduler(),
            cancel_manager=self.get_cancel_manager(),
            action_module=action_module,
            memory_module=memory_module,
            subscribe_module=subscribe_module,
            filter_module=filter_module,
            vision_module=vision_module,
            prompt_module=prompt_module,
        )

    def get_messaging_service(self):
        from mini.messaging.service import MessagingService

        return MessagingService(
            database_manager=self.database_manager,
            context_factory=self.get_context_factory(),
            cancel_manager=self.get_cancel_manager(),
            redis_manager=self.get_redis_manager(),
            bird_manager=BirdMessagingService(),
            instagram_manager=InstagramMessagingService(
                database_manager=self.database_manager
            ),
        )


container = Container()  # Global instance of the container
