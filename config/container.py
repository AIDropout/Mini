from functools import lru_cache

from config.config import config
from mini.agent.modules.memory import MemoryManager
from mini.core.logger import get_logger
from mini.core.rate_limiter import RateLimiter
from mini.database.database import DatabaseManager
from mini.database.tables.user_service import UserTableService
from mini.database.tables.agent_service import AgentTableService
from mini.database.tables.job_service import JobTableService
from mini.llm import LLMService, Model
from mini.messaging.paywall import PaywallService
from mini.messaging.service import MessagingService
from mini.payment.stripe import CheckoutManager, CustomerManager, SubscriptionManager
from mini.server.redis.redis import RedisManager
from mini.utils.time import TimeManager
from mini.messaging.providers.bird.verification.service import VerifyService
from mini.database.tables.room_service import RoomTableService
from mini.payment.service import PaymentService


logger = get_logger(__name__)


class Container:
    def __init__(self):
        self.database_manager = DatabaseManager()
        self.system_time_manager = TimeManager(
            user_timezone=config.TIME_CONFIG.system_timezone
        )
        self.user_time_manager = TimeManager(
            user_timezone=config.TIME_CONFIG.default_timezone
        )
        self.checkout_manager = CheckoutManager()
        self.customer_manager = CustomerManager.from_config(config)
        self.subscription_manager = SubscriptionManager()
        self.verify_service = VerifyService()
        self.redis_manager = RedisManager()

    # --- Table services: ---
    @property
    @lru_cache()
    def user_table_service(self):
        return UserTableService(
            database_manager=self.database_manager,
            customer_manager=self.customer_manager,
        )

    @property
    @lru_cache()
    def agent_table_service(self):
        return AgentTableService(database_manager=self.database_manager)

    @property
    @lru_cache()
    def room_table_service(self):
        return RoomTableService(
            database_manager=self.database_manager,
            customer_manager=self.customer_manager,
            user_table_service=self.user_table_service,
            agent_table_service=self.agent_table_service,
        )

    @property
    @lru_cache()
    def job_table_service(self):
        return JobTableService(
            database_manager=self.database_manager,
            time_manager=self.system_time_manager,
        )

    # --- Other services: ---
    @property
    @lru_cache
    def paywall_service(self):
        return PaywallService(
            database_manager=self.database_manager,
            room_service=self.room_table_service,
        )

    @property
    @lru_cache
    def rate_limiter(self):
        return RateLimiter(redis_manager=self.redis_manager, max_calls=20, period=300)

    @property
    @lru_cache()
    def messaging_service(self):
        return MessagingService(
            database_manager=self.database_manager,
            user_table_service=self.user_table_service,
            system_time_manager=self.system_time_manager,
        )

    @property
    @lru_cache()
    def memory_manager(self):
        return MemoryManager(
            user_id=None,
            agent_id=None,
            time_manager=self.system_time_manager,
            llm_manager=self.llm_service,
            memory_save_delay=5,
        )

    @property
    @lru_cache()
    def llm_service(self):
        return LLMService(
            model=Model.from_model_name(config.MEMORY_GENERAL_LLM),
        )

    @property
    @lru_cache()
    def payment_service(self):
        return PaymentService(
            database_manager=self.database_manager,
            checkout_manager=self.checkout_manager,
            customer_manager=self.customer_manager,
            subscription_manager=self.subscription_manager,
        )


container = Container()  # Global instance of the container
