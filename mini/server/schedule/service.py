from datetime import datetime
from uuid import uuid4

from config.container import container
from mini.agent.tasks.models import MessageTask
from mini.core.logger import get_logger
from mini.database.database import DatabaseManager
from mini.messaging.models import MessagingProviderEnum, ResponseTypeEnum
from mini.messaging.service import MessagingService

logger = get_logger(__name__)


class ProactiveService:
    def __init__(
        self,
        database_manager: DatabaseManager,
        messaging_service: MessagingService,
    ):

        self.database_manager = database_manager
        self.messaging_service = messaging_service

    def send_proactive_message(self, room_id: str, provider: MessagingProviderEnum):
        message_id = str(uuid4())
        task = MessageTask(
            message_id=message_id,
            provider=provider,
            created_at=datetime.now(),
            scheduled_time=datetime.now(),
            request_body={},
            response_type=ResponseTypeEnum.PROACTIVE,  # TODO: clean up MessageTask
        )

        return self.process_proactive_task(room_id, task, self.messaging_service)

    def process_proactive_task(
        self, room_id: str, task: MessageTask, messaging_service
    ):
        from mini.messaging.service import MessagingService  # To avoid circular import

        if not isinstance(messaging_service, MessagingService):
            raise TypeError("messaging_service must be an instance of MessagingService")

        """Internal logic for processing a proactive task"""
        context = messaging_service.context_factory.create_cron_context(room_id)
        messaging_provider = messaging_service.providers.get(task.provider)

        messaging_provider.set_receiver(context.user.phone_number)
        messaging_provider.set_sender(context.agent.bird_channel_id)

        agent = container.get_agent_controller()
        agent.configure(
            messaging_manager=messaging_provider,
            agent=context.agent,
            user=context.user,
            room=context.room,
        )

        success = agent.send_proactive_message()
        if success:
            logger.info("Agent processing finished successfully.")

        return success
