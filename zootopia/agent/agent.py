from zootopia.core.schema import ActionType, RoomTableModel, ZootopiaMessage, ChatTask, RespondChatTask, ReviveChatTask, ScheduledChatTask
from config.config import Config, IntentManagerConfig, ActionManagerConfig, MemoryManagerConfig, FilterConfig
from zootopia.platform.platform import MessageProviderBase
from zootopia.storage.database.supabase import SupabaseDB

# from zootopia.agent.filter.filter import MessageFilter
from zootopia.context import BaseContextManager
from zootopia.agent.intent import IntentManager
from zootopia.agent.action import ActionManager
from zootopia.agent.memory import MemoryManager

from zootopia.core.logger import logger
from zootopia.core.utils.utils import get_current_time_readable



class Agent:
    def __init__(
        self, 
        messaging_service: MessageProviderBase,
        database_service: SupabaseDB,
        room: RoomTableModel,
        filter_config: FilterConfig, 
        intent_config: IntentManagerConfig, 
        action_config: ActionManagerConfig, 
        memory_config: MemoryManagerConfig,
        base_prompt: str
    ) -> None:
        self.base_prompt = base_prompt
        # self.filter = MessageFilter.from_config(filter_config)
        self.intent = IntentManager.from_config(intent_config)
        self.action = ActionManager.from_config(action_config, messaging_service)
        self.memory = MemoryManager.from_config(memory_config, database_service, room)

    @classmethod
    def from_config(cls, config: Config, context: BaseContextManager) -> "Agent":
        return cls(
            messaging_service=context.messaging_service,
            database_service=context.database,
            room=context.room,
            filter_config=config.BEHAVIORS_CONFIG.FILTER,
            intent_config=config.BEHAVIORS_CONFIG.INTENT_MANAGER,
            action_config=config.BEHAVIORS_CONFIG.ACTION_MANAGER,
            memory_config=config.BEHAVIORS_CONFIG.MEMORY_MANAGER,
            base_prompt=context.agent.prompt
        )

    async def handle_chat_task(self, task: ChatTask) -> bool:
        logger.info(task.message)  
        logger.info(task)

        try:
            if isinstance(task, RespondChatTask):
                self.memory.store_message(from_user=True, message=task.instructions)
                # TODO: Add a message filter

            recent_messages = self.memory.get_recent_messages(count=task.recent_message_count)

            prompt_template = """
            {base_prompt}

            Your task: {instructions}

            It is now {current_time}
            """

            system_prompt = prompt_template.format(
                base_prompt=self.base_prompt,
                instructions=task.instructions,
                current_time=get_current_time_readable()
            )

            logger.info(f"\nSystem prompt: {system_prompt}\n")
            logger.info(f"\nRecent messages: {recent_messages}\n")
            sent_response = await self.action.generate_and_send_message(recent_messages, system_prompt)
            
            if sent_response:
                self.memory.store_message(from_user=False, message=sent_response)

            return sent_response

        except Exception as e:
            logger.error(f"Error in processing chat: {str(e)}")
            return None

        # Implement these back in later
        # actions = self.intent.produce_actions(recent_messages + [task.input_context], task.possible_actions or [])
        # results, agent_response = await self.action.execute_actions(actions, recent_messages + [task.input_context])
        # self.memory.update_memory(results)
   