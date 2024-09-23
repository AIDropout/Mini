from mini.core.task.chat import ProactiveTask
from mini.core.logger import get_logger
from mini.database.database import DatabaseManager
from mini.messaging.models import MessagingProviderEnum
from mini.agent.run_agent import run_agent
from mini.messaging.context import ContextFactory
from mini.server.redis import RedisManager
from mini.server.cancel import CancelManager
from mini.messaging.discord.discord import discord_manager


logger = get_logger(__name__)


class ProactiveService:
    def __init__(
        self,
        database_manager: DatabaseManager,
        redis_manager: RedisManager,
        context_factory: ContextFactory,
        cancel_manager: CancelManager,
    ):

        self.database_manager = database_manager
        self.redis_manager = redis_manager
        self.context_factory = context_factory
        self.cancel_manager = cancel_manager

    def send_proactive_message(self, room_id: str, provider: MessagingProviderEnum):
        task = None
        try:
            context = self.context_factory.get_context_from_room_id(room_id)

            task = ProactiveTask(
                context=context,
                provider=provider,
            )

            self.redis_manager.set(
                key=f"{room_id}:{task.id}",
                value=task.model_dump_json(),
                expiry=120,
            )

            run_agent.apply_async(args=[room_id, task.id])
        except Exception as e:
            if room_id and task.id:
                self.cancel_manager.remove_task(room_id, task.id)
            msg = discord_manager.log_error(f"room_id={room_id}")
            logger.exception(msg)
