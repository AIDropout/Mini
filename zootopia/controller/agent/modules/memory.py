from zootopia.core.logger import logger
from zootopia.core.schema.tables import (
    Tables,
    Message,
)
from typing import List, Dict
from zootopia.manager.database import DatabaseManager
from zootopia.core.error import error_handler
from zootopia.controller.agent.modules.base import AgentModule


class MemoryModule(AgentModule):
    def __init__(self, database_manager: DatabaseManager):
        super().__init__(database_manager)

    @error_handler("MemoryModule")
    def get_recent_messages(self, count: int = 10) -> List[Dict[str, str]]:
        """
        Get the most recent messages for a given room ID.

        Args:
        - count (int): The number of recent messages to fetch. Defaults to 10.

        Returns:
        - List[Dict[str, str]]: A list of dictionaries with 'role' and 'content' keys.
        """
        messages = self.database_manager.get_multiple_rows(
            table_name=Tables.MESSAGES.value,
            max_rows=count,
            order_by=Tables.MESSAGES__created_at.value,
            order_desc=True,
            conditions={Tables.MESSAGES__room_id.value: self.room.id},
        )

        if not messages or not isinstance(messages, list):
            logger.warning(
                f"Invalid or empty data fetched for room {self.room.id}: {messages}"
            )
            return []

        # Convert database results to Message instances and then to dict format
        message_models = [Message.model_validate(message) for message in messages]
        message_models.reverse()

        return [
            {
                "role": "assistant" if msg.sender_id == self.agent.id else "user",
                "content": msg.content,
            }
            for msg in message_models
        ]
