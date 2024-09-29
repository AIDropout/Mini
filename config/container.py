from functools import lru_cache
from typing import Any

from config.config import config
from mini.agent.modules.memory import MemoryManager
from mini.agent.modules.proactive import ScheduleDispatch
from mini.core.logger import get_logger
from mini.core.rate_limiter import RateLimiter
from mini.database.database import DatabaseManager
from mini.database.tables.user_service import UserTableService
from mini.database.tables.agent_service import AgentTableService
from mini.llm import LLMService, Model
from mini.messaging.paywall import PaywallService
from mini.messaging.service import MessagingService
from mini.payment.stripe import CheckoutManager, CustomerManager, SubscriptionManager
from mini.server.redis.redis import RedisManager
from mini.server.schedule.apscheduler import APScheduler
from mini.server.schedule.scheduler import Scheduler
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

    @lru_cache()
    def __getattr__(self, name: str) -> Any:
        method_name = f"get_{name}"
        if hasattr(self, method_name):
            return getattr(self, method_name)()
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )

    @lru_cache
    def get_paywall_service(self):
        return PaywallService(
            database_manager=self.database_manager,
            room_service=self.get_room_table_service(),
        )

    @lru_cache
    def get_schedule_dispatch(self):
        return ScheduleDispatch(
            database_manager=self.database_manager,
            scheduler=self.get_scheduler(),
        )

    @lru_cache
    def get_apscheduler(self):
        return APScheduler(db_url=config.SCHEDULER_DB_URL)

    @lru_cache
    def get_scheduler(self):
        return Scheduler(self.get_apscheduler(), self.system_time_manager)

    @lru_cache
    def get_rate_limiter(self):
        return RateLimiter(
            redis_manager=self.get_redis_manager(), max_calls=20, period=300
        )

    @lru_cache()
    def get_redis_manager(self):
        return RedisManager()

    @lru_cache()
    def get_user_table_service(self):
        return UserTableService(
            database_manager=self.database_manager,
            customer_manager=self.customer_manager,
        )

    @lru_cache()
    def get_agent_table_service(self):
        return AgentTableService(database_manager=self.database_manager)

    @lru_cache()
    def get_messaging_service(self):
        return MessagingService(
            database_manager=self.database_manager,
            user_table_service=self.get_user_table_service,
            system_time_manager=self.system_time_manager,
        )

    @lru_cache()
    def get_memory_manager(self):
        return MemoryManager(
            user_id=None,
            agent_id=None,
            time_manager=self.system_time_manager,
            llm_manager=self.get_llm_service(),
            memory_save_delay=5,
        )

    @lru_cache()
    def get_llm_service(self):
        return LLMService(
            model=Model.from_model_name(config.MEMORY_GENERAL_LLM),
        )

    @lru_cache()
    def get_verify_service(self):
        return VerifyService()

    @lru_cache()
    def get_room_table_service(self):
        return RoomTableService(
            database_manager=self.database_manager,
            customer_manager=self.customer_manager,
            user_table_service=self.get_user_table_service(),
            agent_table_service=self.get_agent_table_service(),
        )

    @lru_cache()
    def get_payment_service(self):
        return PaymentService(
            database_manager=self.database_manager,
            checkout_manager=self.checkout_manager,
            customer_manager=self.customer_manager,
            subscription_manager=self.subscription_manager,
        )


container = Container()  # Global instance of the container
