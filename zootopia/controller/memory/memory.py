from zootopia.core.logger import logger
from zootopia.core.schema import Tables, MessageTableModel
from typing import List, Dict
from config.config import MemoryManagerConfig
from zootopia.storage.database.supabase import SupabaseDB
from zootopia.core.schema import Tables, RoomTableModel

class MemoryManager:
    def __init__(self, database_service: SupabaseDB, room_id: int):
        self.database_service = database_service
        self.room_id = room_id

    @classmethod
    def from_config(cls, config: MemoryManagerConfig, database_service: SupabaseDB, room_data: RoomTableModel) -> "MemoryManager":
        database_service = database_service
        room_id = room_data.id
        return cls(
            database_service, room_id
        )

    def store_message(self, from_user: bool, message: str):
        """Inserts user's message into database"""
        try:
            message = MessageTableModel(
                room_id=self.room_id,
                from_user=from_user,
                message=message
            )
            stored_message = self.database_service.insert(Tables.MESSAGES.value, message)
            logger.info(f"Message stored successfully. ID: {stored_message.id}")
            return stored_message
        except Exception as e:
            logger.error(f"Error storing message: {str(e)}")
            raise
            
    def get_recent_messages(self, count: int = 10) -> List[Dict[str, str]]:
        """
        Get the most recent messages for a given room ID in a format suitable for LLM input.
        Multiple consecutive user messages are combined with a pipe symbol.

        Args:
        - count (int): The number of recent messages to fetch. Defaults to 10.

        Returns:
        - List[Dict[str, str]]: A list of dictionaries with 'role' and 'content' keys.
        """
        try:
            messages = self.database_service.get_multiple_rows(
                table_name=Tables.MESSAGES.value,
                max_rows=count,
                order_by=Tables.MESSAGES__created_at.value,
                order_desc=True,
                conditions={Tables.MESSAGES__room_id.value: self.room_id}
            )
            
            # Convert database results to MessageTableModel instances
            message_models = [MessageTableModel.model_validate(message) for message in messages]

            message_models.reverse()
            
            # Convert to LLM friendly format
            llm_messages = []
            for msg in message_models:
                role = "user" if msg.from_user else "assistant"
                content = msg.message
                
                if llm_messages and llm_messages[-1]['role'] == "user" and role == "user":
                    # If the current message is from a user and the last message was also from a user,
                    # append the content with a pipe symbol
                    llm_messages[-1]['content'] += f" | {content}"
                else:
                    # Otherwise, add a new message entry
                    llm_messages.append({"role": role, "content": content})

            return llm_messages
        except Exception as e:
            logger.error(f"Error fetching recent messages for room {self.room_id}: {str(e)}")
            return []

    def update_memory(self, results):
        logger.info("Updating general memory")
        pass

    def retrieve_memory(self, query):
        logger.info(f"Retrieving memory for query: {query}")
        pass

    def store_memory(self, data):
        logger.info("Storing new memory")
        pass