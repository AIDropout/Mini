from zootopia.core.logger import logger
from zootopia.core.schema import ActionType, RoomTableModel, ZootopiaMessage
from config.config import Config, IntentManagerConfig, ActionManagerConfig, MemoryManagerConfig, FilterConfig
from zootopia.platform.platform import MessageProviderBase
from zootopia.storage.database.supabase import SupabaseDB

# from zootopia.agent.filter.filter import MessageFilter
from zootopia.agent.context import ContextManager
from zootopia.agent.intent import IntentManager
from zootopia.agent.action import ActionManager
from zootopia.agent.memory import MemoryManager
from zootopia.agent.tasks.tasks import ChatTask, UserMessageTask, ChatReviverTask, ScheduledTask
from zootopia.core.utils.utils import get_current_time_readable



class Agent:
    def __init__(
        self, 
        message: ZootopiaMessage,
        messaging_service: MessageProviderBase,
        database_service: SupabaseDB,
        room: RoomTableModel,
        filter_config: FilterConfig, 
        intent_config: IntentManagerConfig, 
        action_config: ActionManagerConfig, 
        memory_config: MemoryManagerConfig,
        base_prompt: str
    ) -> None:
        self.message = message
        self.base_prompt = base_prompt
        # self.filter = MessageFilter.from_config(filter_config)
        self.intent = IntentManager.from_config(intent_config)
        self.action = ActionManager.from_config(action_config, messaging_service)
        self.memory = MemoryManager.from_config(memory_config, database_service, room)

    @classmethod
    def from_config(cls, context: ContextManager, config: Config) -> "Agent":
        return cls(
            message=context.message,
            messaging_service=context.messaging_service,
            database_service=context.database,
            room=context.room,
            filter_config=config.BEHAVIORS_CONFIG.FILTER,
            intent_config=config.BEHAVIORS_CONFIG.INTENT_MANAGER,
            action_config=config.BEHAVIORS_CONFIG.ACTION_MANAGER,
            memory_config=config.BEHAVIORS_CONFIG.MEMORY_MANAGER,
            base_prompt=context.agent.prompt
        )
    
    # Chat responder (reactive)
    # Get past messages + incoming message, formulate response, send it

    # Chat reviver (proactive)
    # Get past messages + context about chat silence, formulate response, send it

    # Chat scheduler (proactive)
    # Get past messages + scheduled context, formulate response, send it
    async def respond_to_user(self) -> bool:
        task = UserMessageTask(self.message)
        return await self._process_chat(task)

    async def revive_chat(self) -> bool:
        task = ChatReviverTask()
        return await self._process_chat(task)

    async def handle_scheduled_task(self) -> bool:
        task = ScheduledTask()
        return await self._process_chat(task)

    async def _process_chat(self, task: ChatTask) -> bool:
        try:
            if isinstance(task, UserMessageTask):
                self.memory.store_message(from_user=True, message=task.instructions)
                # TODO: Add a message filter

            recent_messages = self.memory.get_recent_messages(count=task.recent_message_count)
            logger.info(f"Recent messages: {recent_messages}")

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

            sent_response = await self.action.generate_and_send_message(system_prompt, recent_messages)
            
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
   