
from zootopia.controller.context.context import ContextManager
from zootopia.core.logger import logger
from zootopia.core.schema import Tables, MessageTableModel
from typing import List, Dict


class MemoryManager:
    def __init__(self, context: ContextManager):
        self.context = context

    def store_message(self, from_user: bool, message: str):
        """Inserts user's message into database"""
        try:
            message = MessageTableModel(
                room_id=self.context.room.id,
                from_user=from_user,
                message=message
            )
            stored_message = self.context.database.insert(Tables.MESSAGES.value, message)
            logger.info(f"Message stored successfully. ID: {stored_message.id}")
            return stored_message
        except Exception as e:
            logger.error(f"Error storing message: {str(e)}")
            raise
        
    def get_recent_messages(self, count: int = 10) -> List[Dict[str, str]]:
        """
        Get the most recent messages for a given room ID in a format suitable for LLM input.

        Args:
        - count (int): The number of recent messages to fetch. Defaults to 10.

        Returns:
        - List[Dict[str, str]]: A list of dictionaries with 'role' and 'content' keys.
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

            message_models.reverse()
            
            # Convert to LLM friendly format
            llm_messages = []
            prev_role = None
            for msg in message_models:
                role = "user" if msg.from_user else "assistant"
                content = msg.message
                
                if role == prev_role == "user":
                    # If two user messages in a row, append with pipe symbol
                    llm_messages[-1]['content'] += f" | {content}"
                else:
                    llm_messages.append({"role": role, "content": content})
                
                prev_role = role

            return llm_messages
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