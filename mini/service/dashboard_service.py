from fastapi import Body
from pydantic import BaseModel, Field

from mini.core.logger import get_logger
from mini.core.schema.tables import Message, Tables
from mini.storage.database import DatabaseManager
from mini.manager.messaging import MessagingManagerFactory
from mini.service.base import Service
from mini.service.context_factory import ContextFactory

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

    def send_admin_message(self, room_id: str, message: str):

        context = self.context_factory.create_cron_context(room_id)

        bird_manager = self.messaging_manager_factory.bird_manager
        bird_manager.set_receiver(context.user.phone_number)
        bird_manager.set_sender(context.agent.bird_channel_id)
        success = bird_manager.send_message(text=message)

        if success:
            new_message = Message(
                sender_id=context.room.agent_id,
                room_id=room_id,
                content=message,
                sent_by_admin=True,
            )

            self.database_manager.insert(Tables.MESSAGES, new_message)
