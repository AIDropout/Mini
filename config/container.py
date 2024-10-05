from functools import cached_property

from config.config import config
from mini.core.logger import get_logger
from mini.core.rate_limiter import RateLimiter
from mini.database.database import DatabaseManager
from mini.database.tables.agent_service import AgentTableService
from mini.database.tables.job_service import JobTableService
from mini.database.tables.room_service import RoomTableService
from mini.database.tables.user_service import UserTableService
from mini.database.tables.message_service import MessageTableService
from mini.database.tables.session_service import SessionTableService
from mini.database.tables.subscription_service import SubscriptionTableService
from mini.llm import LLMService, Model
from mini.messaging.paywall import PaywallService
from mini.messaging.providers.bird.verification.service import VerifyService
from mini.messaging.service import MessagingService
from mini.messaging.factory import MessageTaskFactory
from mini.payment.service import PaymentService
from mini.payment.stripe import CheckoutManager, CustomerManager, SubscriptionManager
from mini.server.redis.redis import RedisManager
from mini.utils.time import TimeManager

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
    @cached_property
    def user_table_service(self):
        return UserTableService(
            database_manager=self.database_manager,
            customer_manager=self.customer_manager,
        )

    @cached_property
    def agent_table_service(self):
        return AgentTableService(database_manager=self.database_manager)

    @cached_property
    def room_table_service(self):
        return RoomTableService(
            database_manager=self.database_manager,
            customer_manager=self.customer_manager,
            user_table_service=self.user_table_service,
            agent_table_service=self.agent_table_service,
            session_table_service=self.session_table_service,
            system_time_manager=self.system_time_manager,
        )

    @cached_property
    def job_table_service(self):
        return JobTableService(
            database_manager=self.database_manager,
            system_time_manager=self.system_time_manager,
        )

    @cached_property
    def subscription_table_service(self):
        return SubscriptionTableService(
            database_manager=self.database_manager,
            customer_manager=self.customer_manager,
            user_table_service=self.user_table_service,
            agent_table_service=self.agent_table_service,
        )

    @cached_property
    def message_table_service(self):
        return MessageTableService(
            database_manager=self.database_manager,
        )

    @cached_property
    def session_table_service(self):
        return SessionTableService(
            database_manager=self.database_manager,
            system_time_manager=self.system_time_manager,
        )

    # --- Other services: ---

    @cached_property
    def paywall_service(self):
        return PaywallService(
            database_manager=self.database_manager,
            message_service=self.message_table_service,
        )

    @cached_property
    def rate_limiter(self):
        return RateLimiter(redis_manager=self.redis_manager, max_calls=20, period=300)

    @cached_property
    def messaging_service(self):
        return MessagingService(
            database_manager=self.database_manager,
            user_table_service=self.user_table_service,
            room_table_service=self.room_table_service,
            session_table_service=self.session_table_service,
            message_table_service=self.message_table_service,
            message_task_factory=self.message_task_factory,
        )

    @cached_property
    def message_task_factory(self):
        return MessageTaskFactory(
            database_manager=self.database_manager,
            user_table_service=self.user_table_service,
            system_time_manager=self.system_time_manager,
            message_table_service=self.message_table_service,
            session_table_service=self.session_table_service,
        )

    @cached_property
    def llm_service(self):
        return LLMService(
            model=Model.from_model_name(config.MEMORY_GENERAL_LLM),
        )

    @cached_property
    def payment_service(self):
        return PaymentService(
            checkout_manager=self.checkout_manager,
            customer_manager=self.customer_manager,
            subscription_manager=self.subscription_manager,
            subscription_table_service=self.subscription_table_service,
            user_table_service=self.user_table_service,
        )


container = Container()  # Global instance of the container
