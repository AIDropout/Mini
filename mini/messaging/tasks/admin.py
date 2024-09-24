from config.config import config
from mini.core.exceptions import RoomDisabledByAdminError, CrossedMessageLimitError
from mini.core.logger import get_logger
from mini.messaging.tasks.models import ResponseTask
from mini.database.database import DatabaseManager
from mini.database.service.room_service import RoomService
from mini.messaging.providers.discord import discord_manager
from mini.database.models import Tables, Message

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

    def process_response_task(self, task: ResponseTask) -> ResponseTask:
        self._handle_disabled_room(task)
        self._handle_reset_phrase(task)
        self._handle_subscription_check(task)
        self._insert_user_message(task)
        self._log_to_discord(task)
        return task

    def _handle_disabled_room(self, task: ResponseTask):
        if task.context.room.disabled_by_admin:
            raise RoomDisabledByAdminError(room_id=task.context.room.id)

    def _handle_reset_phrase(self, task: ResponseTask):
        if task.message.content == config.SECRET_PHRASES.reset_user:
            self.database_manager.supabase.auth.admin.delete_user(task.context.user.id)
            self.database_manager.delete(
                Tables.USERS, {Tables.USERS__id: task.context.user.id}
            )
            task.messaging_provider.send_message(
                text="Successfully deleted your user from Auth tables and Users table"
            )
            return

    def _insert_user_message(self, task: ResponseTask):
        self.database_manager.insert(
            Tables.MESSAGES,
            Message(
                room_id=task.context.room.id,
                sender_id=task.context.user.id,
                content=task.message.content,
            ),
        )

    def _log_to_discord(self, task: ResponseTask):
        if config.ENVIRONMENT == "production":
            discord_manager.log_message(
                message=f"-# {task.context.user.phone_number} -> {task.context.agent.name}: {task.message.content}"
            )

    def _handle_subscription_check(self, task: ResponseTask):
        agent_message_count = self.room_service.get_message_count_for_sender(
            task.context.room.id, task.context.agent.id
        )

        if (
            agent_message_count >= task.context.agent.free_msg_limit
            and not task.context.user.is_subscribed
        ):
            if task.context.room.subscribe_msg_sent:
                raise CrossedMessageLimitError(room_id=task.context.room.id)
            else:
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
