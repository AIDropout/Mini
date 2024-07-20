from zootopia.core.logger import logger
from zootopia.core.schema import ActionType, RoomTableModel

from config.config import Config, IntentManagerConfig, ActionManagerConfig, MemoryManagerConfig
from zootopia.platform.platform import MessageProviderBase
from zootopia.storage.database.supabase import SupabaseDB

from zootopia.controller.context import ContextManager
from zootopia.controller.intent import IntentManager
from zootopia.controller.action import ActionManager
from zootopia.controller.memory import MemoryManager


class AgentController:
    def __init__(
        self, 
        message: str,
        messaging_service: MessageProviderBase,
        database_service: SupabaseDB,
        room: RoomTableModel,
        intent_config: IntentManagerConfig, 
        action_config: ActionManagerConfig, 
        memory_config: MemoryManagerConfig,
    ) -> None:
        self.message = message
        self.intent = IntentManager.from_config(intent_config)
        self.action = ActionManager.from_config(action_config, messaging_service)
        self.memory = MemoryManager.from_config(memory_config, database_service, room)

    @classmethod
    def from_config(cls, context: ContextManager, config: Config) -> "AgentController":
        message = context.message.content
        messaging_service = context.messaging_service
        database_service = context.database
        room = context.room
        intent_config = config.BEHAVIORS_CONFIG.INTENT_MANAGER
        action_config = config.BEHAVIORS_CONFIG.ACTION_MANAGER
        memory_config = config.BEHAVIORS_CONFIG.MEMORY_MANAGER
        return cls( 
            message, messaging_service, database_service, room, intent_config, action_config, memory_config
        )

    async def handle_message(self):
        try:
            # Insert message
            self.memory.store_message(
                from_user=True, 
                message=self.message
            )

            # Produce list of actions based on recent messages
            recent_messages = self.memory.get_recent_messages(count=10)
            print(recent_messages)
            possible_actions = [
                ActionType.RECALL,
                ActionType.WEB_SEARCH,
            ]

            # Intent layer to determine actions
            actions = self.intent.produce_actions(recent_messages, possible_actions)
            
            # Execute the actions
            results, agent_response = await self.action.execute_actions(actions, recent_messages)
            
            # Update general memory with the results (Not Implemented)
            self.memory.update_memory(results)
            
            if agent_response:
                self.memory.store_message(
                    from_user=False, 
                    message=agent_response
                )
                        
        except Exception as e:
            logger.error(f"Error in handling message: {str(e)}")