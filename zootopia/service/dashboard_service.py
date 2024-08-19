from zootopia.manager.database import DatabaseManager
from zootopia.manager.messaging import MessagingManagerFactory
from zootopia.core.schema import Message, Tables
from zootopia.service.context_factory import ContextFactory
from zootopia.core.logger import get_logger
from zootopia.service.base import Service
from pydantic import BaseModel, Field


logger = get_logger(__name__)


class AdminMessageRequest(BaseModel):
    room_id: str = Field(
        ..., description="The ID of the room to send the admin message to"
    )
    message: str = Field(..., description="The content of the admin message to be sent")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "room_id": "room_123456",
                    "message": "This is an important announcement from the admin.",
                }
            ]
        }
    }


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

    async def send_admin_message(self, request: AdminMessageRequest):
        room_id = request.room_id
        message = request.message

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
