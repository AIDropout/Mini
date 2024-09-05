from typing import Dict, List

from mini.controller.agent.modules.base import AgentModule
from mini.core.error import error_handler
from mini.core.logger import get_logger
from mini.core.schema.memory import MemoryRecordSchema
from mini.core.schema.tables import Message, Tables
from mini.manager.database import DatabaseManager
from mini.manager.llm import LLMManager
from mini.manager.memory import MemoryManager

logger = get_logger(__name__)


class MemoryModule(AgentModule):
    def __init__(
        self,
        database_manager: DatabaseManager,
        memory_manager: MemoryManager,
        llm_manager: LLMManager,
    ):
        super().__init__(database_manager)
        self.memory_manager = memory_manager
        self.llm_manager = llm_manager

    def _set_user_and_agent_id(
        self, user_id: str | None = None, agent_id: str | None = None
    ):
        if user_id is None:
            user_id = self.user.phone_number
        if agent_id is None:
            agent_id = self.agent.id

        logger.info(
            "Setting user_id (%s) and agent_id (%s) for memory manager",
            user_id,
            agent_id,
        )

        self.memory_manager.set_user_id(user_id)
        self.memory_manager.set_agent_id(agent_id)

    def _prepare_recent_messages(self, recent_messages: List[Dict[str, str]]) -> str:
        formatted_messages = [
            f"{msg['role']}: {msg['content']}" for msg in recent_messages
        ]
        return "\n".join(formatted_messages)

    def get_relevant_memories(self, recent_messages: List[Dict[str, str]]) -> List[str]:
        self._set_user_and_agent_id()
        prepared_recent_messages = self._prepare_recent_messages(recent_messages)
        memories: List[MemoryRecordSchema] = self.memory_manager.get_memory(
            prepared_recent_messages
        )

        cleaned = []
        for memory in memories:
            created_at_str = (
                memory.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if memory.created_at
                else "N/A"
            )
            updated_at_str = (
                memory.updated_at.strftime("%Y-%m-%d %H:%M:%S")
                if memory.updated_at
                else "N/A"
            )

            cleaned_memory = (
                f"Memory: {memory.memory}\n"
                f"Metadata: {memory.metadata}\n"
                f"Created At: {created_at_str}\n"
                f"Memory Last Updated At: {updated_at_str}"
            )

            cleaned.append(cleaned_memory)

        logger.info("Memories: %s", cleaned)

        return cleaned

    def save_relevant_memories(self, save_interval: int = 10) -> str:
        self._set_user_and_agent_id()

        count_messages = self.database_manager.count_rows(table_name=Tables.MESSAGES)
        remaining_messages_until_save = count_messages % save_interval

        logger.info(
            "There have been %s messages total. Next save will occur in %s messages.",
            count_messages,
            remaining_messages_until_save,
        )

        if remaining_messages_until_save in [0, 1]:
            messages_for_memory = self.get_recent_messages(count=max(save_interval) + 2)
            prepared_messages = self._prepare_recent_messages(messages_for_memory)
            self.memory_manager.add_memory(data=prepared_messages)
            logger.info(
                "Saved data from %s messages for memory.", len(messages_for_memory)
            )

    @error_handler("MemoryModule")
    def get_recent_messages(self, count: int = 20) -> List[Dict[str, str]]:
        """
        Get the most recent messages for a given room ID.

        Args:
        - count (int): The number of recent messages to fetch. Defaults to 10.

        Returns:
        - List[Dict[str, str]]: A list of dictionaries with 'role' and 'content' keys.
        """
        messages = self.database_manager.get_multiple_rows(
            table_name=Tables.MESSAGES,
            max_rows=count,
            order_by=Tables.MESSAGES__created_at,
            order_desc=True,
            conditions={Tables.MESSAGES__room_id: self.room.id},
        )

        if not messages or not isinstance(messages, list):
            logger.warning(
                "Invalid or empty data fetched for room %s: %s", self.room.id, messages
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
