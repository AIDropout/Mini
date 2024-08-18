from zootopia.manager.database import DatabaseManager
from zootopia.manager.messaging import MessagingManagerFactory
from zootopia.core.schema import Message, Tables
from zootopia.service.context_factory import ContextFactory
from zootopia.core.logger import get_logger
from zootopia.service.base import Service

logger = get_logger(__name__)


class DashboardService(Service):
    def __init__(
        self,
        database_manager: DatabaseManager,
        messaging_manager_factory: MessagingManagerFactory,
        context_factory: ContextFactory,
    ):
        super().__init__(database_manager)
        self.messaging_manager_factory = messaging_manager_factory
        self.context_factory = context_factory

    # TODO: Define the Request
    async def send_admin_message(self, payload: dict):
        room_id = payload.get("room_id")
        message = payload.get("message")

        if not room_id or not message:
            raise ValueError("Missing room_id or message")

        context = self.context_factory.create_cron_context(room_id)

        bird_manager = self.messaging_manager_factory.bird_manager
        bird_manager.set_receiver(context.user.phone_number)
        bird_manager.set_sender(context.agent.bird_channel_id)
        success = await bird_manager.send_message(message)

        if success:
            new_message = Message(
                sender_id=context.room.agent_id,
                room_id=room_id,
                content=message,
                sent_by_admin=True,
            )

            self.database_manager.insert(Tables.MESSAGES.value, new_message)
