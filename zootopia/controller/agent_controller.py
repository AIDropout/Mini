from zootopia.core.logger import logger
from zootopia.core.schema import ActionType

from zootopia.controller.context import ContextManager
from zootopia.controller.intent import IntentManager
from zootopia.controller.action import ActionManager
from zootopia.controller.memory import MemoryManager


class AgentController:
    def __init__(
        self, 
        context: ContextManager
    ) -> None:
        self.context = context
        self.intent = IntentManager.from_config(context)
        self.action = ActionManager.from_config(context)
        self.memory = MemoryManager(context)

    async def handle_message(self):
        try:
            # Insert message
            self.memory.store_message(
                from_user=True, 
                message=self.context.message.content
            )

            # Produce list of actions based on recent messages
            recent_messages = self.memory.get_recent_messages(count=10)
            possible_actions = [
                ActionType.RECALL,
                ActionType.WEB_SEARCH,
            ]

            # Intent layer to determine actions
            actions = self.intent.produce_actions(recent_messages, possible_actions)
            
            # Execute the actions
            results, agent_response = await self.action.execute_actions(actions, recent_messages)
            
            # Update general memory with the results
            self.memory.update_memory(results)
            
            self.memory.store_message(
                from_user=False, 
                message=agent_response
            )
                        
        except Exception as e:
            logger.error(f"Error in handling message: {str(e)}")