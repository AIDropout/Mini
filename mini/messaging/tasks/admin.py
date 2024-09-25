from config.config import config
from mini.core.exceptions import CrossedMessageLimitError
from mini.core.logger import get_logger
from mini.messaging.tasks.models import ResponseTask
from mini.database.database import DatabaseManager
from mini.database.service.room_service import RoomService
from mini.database.models import Tables

logger = get_logger(__name__)


class MessagingAdminService:
    """
    Handles administrative tasks like special return cases, subscribe logic, and logging/storing to DB.
    """

    def __init__(
        self, database_manager: DatabaseManager, room_service: RoomService
    ) -> None:
        self.database_manager = database_manager
        self.room_service = room_service

    def handle_subscription_check(self, task: ResponseTask) -> None:
        """
        User subscription logic. Sends a subscribe message if user has crossed the messaging limit.
        """
        if task.context.user.is_subscribed:
            return

        agent_message_count = self.room_service.get_message_count_for_sender(
            task.context.room.id, task.context.agent.id
        )

        if agent_message_count >= task.context.agent.free_msg_limit:
            if not task.context.room.subscribe_msg_sent:
                message = (
                    f"{task.context.agent.subscribe_msg}\n"
                    f"{config.FRONTEND_URL}/subscribe"
                )

                task.messaging_provider.send_message(message)

                self.database_manager.update(
                    Tables.ROOMS,
                    {
                        Tables.ROOMS__subscribe_msg_sent: True,
                    },
                    condition_key=Tables.ROOMS__id,
                    condition_value=task.context.room.id,
                )

            raise CrossedMessageLimitError(room_id=task.context.room.id)
