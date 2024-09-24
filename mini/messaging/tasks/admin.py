"""Handles administrative tasks like special return cases, subscribe logic, and logging/storing to DB"""

from config.config import config
from mini.core.logger import get_logger
from mini.core.models.task.chat import ResponseTask
from mini.database.database import DatabaseManager
from mini.messaging.providers.discord import discord_manager
from mini.database.models import Tables, Message

logger = get_logger(__name__)


class MessagingAdminService:
    def __init__(self, database_manager: DatabaseManager) -> None:
        self.database_manager = database_manager

    def process_response_task(self, task: ResponseTask) -> ResponseTask:
        self._handle_disabled_room(task)
        self._handle_reset_phrase(task)
        self._insert_user_message(task)
        self._log_to_discord(task)
        return task

    def _handle_disabled_room(self, task: ResponseTask):
        if task.context.room.disabled_by_admin:
            logger.warning(f"Room {task.context.room.id} disabled. Canceling process.")
            raise ValueError("Room disabled by admin")

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






