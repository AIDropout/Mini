from typing import Optional

from config.config import config
from mini.agent.modules.memory import MemoryManager
from mini.agent.modules.proactive import ScheduleDispatch
from mini.core.logger import get_logger
from mini.core.rate_limiter import RateLimiter
from mini.database.database import DatabaseManager
from mini.database.tables.user_service import UserTableService
from mini.llm import LLMService, Model
from mini.messaging.paywall import PaywallService
from mini.messaging.service import MessagingService
from mini.payment.stripe import CheckoutManager, CustomerManager, SubscriptionManager
from mini.server.redis.redis import RedisManager
from mini.server.schedule.apscheduler import APScheduler
from mini.server.schedule.scheduler import Scheduler
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
        self.user_table_service: Optional[UserTableService] = None
        self.messaging_service: Optional[MessagingService] = None
        self.redis_manager: Optional[RedisManager] = None
        self.rate_limiter: Optional[RateLimiter] = None
        self.memory_manager: Optional[MemoryManager] = None
        self.apscheduler: Optional[APScheduler] = None
        self.scheduler: Optional[Scheduler] = None
        self.paywall_service: Optional[PaywallService] = None
        self.scheduler_dispatch: Optional[ScheduleDispatch] = None

    def get_paywall_service(self):
        if self.paywall_service is None:
            self.paywall_service = PaywallService(
                database_manager=self.database_manager,
                room_service=self.get_room_service(),
            )
        return self.paywall_service

    def get_schedule_dispatch(self):
        if self.scheduler_dispatch is None:
            self.scheduler_dispatch = ScheduleDispatch(
                database_manager=self.database_manager,
                scheduler=self.get_scheduler(),
            )
        return self.scheduler_dispatch

    def get_apscheduler(self):
        if self.apscheduler is None:
            self.apscheduler = APScheduler(db_url=config.SCHEDULER_DB_URL)
        return self.apscheduler

    def get_scheduler(self):
        if self.scheduler is None:
            self.scheduler = Scheduler(self.get_apscheduler())
        return self.scheduler

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

    def get_user_table_service(self):
        if self.user_table_service is None:
            self.user_table_service = UserTableService(
                database_manager=self.database_manager,
                customer_manager=self.customer_manager,
            )
        return self.user_table_service

    def get_agent_service(self):
        from mini.database.tables.agent_service import AgentTableService

        return AgentTableService(database_manager=self.database_manager)

    def get_messaging_service(self) -> MessagingService:
        if self.messaging_service is None:
            self.messaging_service = MessagingService(
                database_manager=self.database_manager,
                user_table_service=self.get_user_table_service(),
            )
        return self.messaging_service

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
        from mini.messaging.providers.bird import BirdMessaging
        from mini.messaging.providers.bird.verification.service import VerifyService

        return VerifyService()

    def get_room_service(self):
        from mini.database.tables.room_service import RoomTableService

        return RoomTableService(
            database_manager=self.database_manager,
            customer_manager=self.customer_manager,
            user_table_service=self.get_user_table_service(),
        )

    def get_payment_service(self):
        from mini.payment.service import PaymentService

        return PaymentService(
            database_manager=self.database_manager,
            checkout_manager=self.checkout_manager,
            customer_manager=self.customer_manager,
            subscription_manager=self.subscription_manager,
        )


container = Container()  # Global instance of the container
