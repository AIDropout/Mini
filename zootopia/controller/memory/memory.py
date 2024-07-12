
from zootopia.controller.context.context import ContextManager
from zootopia.core.logger import logger
from zootopia.core.schema import Tables, MessageTableModel
from typing import List


class MemoryManager:
    def __init__(self, context: ContextManager):
        self.context = context

    def store_user_message(self):
        """Inserts user's message into database"""
        try:
            message = MessageTableModel(
                room_id=self.context.room.id,
                from_user=True,
                message=self.context.message.content
            )
            stored_message = self.context.database.insert(Tables.MESSAGES.value, message)
            logger.info(f"Message stored successfully. ID: {stored_message.id}")
            return stored_message
        except Exception as e:
            logger.error(f"Error storing message: {str(e)}")
            raise
        
    def get_recent_messages(self, count: int = 10) -> List[MessageTableModel]:
        """
        Get the most recent messages for a given room ID.

        Args:
        - count (int): The number of recent messages to fetch. Defaults to 10.

        Returns:
        - List[MessageTableModel]: A list of the most recent messages for the room.
        """
        try:
            messages = self.context.database.get_multiple_rows(
                table_name=Tables.MESSAGES.value,
                max_rows=count,
                order_by=Tables.MESSAGES__created_at.value,
                order_desc=True,
                conditions={Tables.MESSAGES__room_id.value: self.context.room.id}
            )
            
            # Convert database results to MessageTableModel instances
            message_models = [MessageTableModel.model_validate(message) for message in messages]

            # Reverse the list to get chronological order (oldest to newest)
            message_models.reverse()

            return message_models
        except Exception as e:
            logger.error(f"Error fetching recent messages for room {self.context.room.id}: {str(e)}")
            return []

    def update_memory(self, results):
        # Implement logic to update general memory based on action results
        logger.info("Updating general memory")
        # TODO: Implement the actual logic for updating general memory
        pass

    def retrieve_memory(self, query):
        # Implement logic to retrieve relevant memories
        logger.info(f"Retrieving memory for query: {query}")
        # TODO: Implement the actual logic for retrieving memory
        pass

    def store_memory(self, data):
        # Implement logic to store new memories
        logger.info("Storing new memory")
        # TODO: Implement the actual logic for storing new memory
        pass