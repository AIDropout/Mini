from datetime import datetime
from uuid import uuid4

from mini.controller.agent_controller import run_agent
from mini.controller.task import ProactiveTask, TaskType
from mini.core.logger import get_logger
from mini.manager.messaging import MessagingManagerFactory
from mini.server.redis.redis import RedisManager
from mini.service.base import Service
from mini.service.context_factory import ContextFactory
from mini.storage.database import DatabaseManager

logger = get_logger(__name__)


class ProactiveService(Service):
    def __init__(
        self,
        database_manager: DatabaseManager,
        messaging_manager_factory: MessagingManagerFactory,
        context_factory: ContextFactory,
        redis_manager: RedisManager,
    ):

        super().__init__(database_manager)
        self.messaging_manager_factory = messaging_manager_factory
        self.context_factory = context_factory
        self.redis_manager = redis_manager

    def send_proactive_message(self, room_id: str):
        context = self.context_factory.create_cron_context(room_id)
        bird_manager = self.messaging_manager_factory.bird_manager
        bird_manager.set_receiver(context.user.phone_number)
        bird_manager.set_sender(context.agent.bird_channel_id)

        task = ProactiveTask(
            id=str(uuid4()),
            scheduled_for=datetime.now(),
            context=context,
        )

        self.redis_manager.set(
            key=f"{room_id}:{task.id}",
            value=task.model_dump_json(),
            expiry=120,
        )

        new_task = run_agent.apply_async(
            args=[room_id, task.id, TaskType.PROACTIVE], countdown=0
        )

        if new_task:
            logger.info(
                f"🟢 Scheduled short-term task in {delay} seconds\n"
                f"🟢 Current time: {datetime.now().isoformat()}\n"
                f"🟢 Scheduled response time: {task.scheduled_for.isoformat()}"
            )
