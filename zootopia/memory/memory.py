from zootopia.core.logger import logger
from zootopia.core.schema import (
    Tables,
    MessageTableModel,
    RoomTableModel,
    AgentTableModel,
)
from typing import List, Dict
from zootopia.services import SupabaseDB
from zootopia.core.error import error_handler


class MemoryManager:

    def __init__(
        self, database_service: SupabaseDB, room: RoomTableModel, agent: AgentTableModel
    ):
        self.database_service = database_service
        self.room_id = room.id
        self.agent_id = agent.id

    @error_handler("MemoryManager")
    def get_recent_messages(self, count: int = 10) -> List[Dict[str, str]]:
        """
        Get the most recent messages for a given room ID.

        Args:
        - count (int): The number of recent messages to fetch. Defaults to 10.

        Returns:
        - List[Dict[str, str]]: A list of dictionaries with 'role' and 'content' keys.
        """
        messages = self.database_service.get_multiple_rows(
            table_name=Tables.MESSAGES.value,
            max_rows=count,
            order_by=Tables.MESSAGES__created_at.value,
            order_desc=True,
            conditions={Tables.MESSAGES__room_id.value: self.room_id},
        )

        if not messages or not isinstance(messages, list):
            logger.warning(
                f"Invalid or empty data fetched for room {self.room_id}: {messages}"
            )
            return []

        # Convert database results to MessageTableModel instances and then to dict format
        message_models = [
            MessageTableModel.model_validate(message) for message in messages
        ]
        message_models.reverse()

        return [
            {
                "role": "assistant" if msg.sender_id == self.agent_id else "user",
                "content": msg.content,
            }
            for msg in message_models
        ]
