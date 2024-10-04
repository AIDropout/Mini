from config.config import config
from mini.core.exceptions import CrossedMessageLimitError
from mini.core.logger import get_logger
from mini.core.models.message_tasks import ResponseTask
from mini.database.database import DatabaseManager
from mini.database.tables.room_service import RoomTableService
from mini.database.tables.message_service import MessageTableService
from mini.database.models import Tables

logger = get_logger(__name__)


class PaywallService:
    """
    Handles paywall logic in messaging.
    """

    def __init__(
        self, database_manager: DatabaseManager, message_service: MessageTableService
    ) -> None:
        self.database_manager = database_manager
        self.message_service = message_service

    def handle_subscription_check(self, task: ResponseTask) -> None:
        """
        User subscription logic. Sends a subscribe message if user has crossed the messaging limit.
        """
        if task.context.user.is_subscribed:
            return
        
        user_message_count = self.message_service.get_user_message_count(task.context.user.id)

        if user_message_count >= config.STRIPE_CONFIG.messages_before_paywall:
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
