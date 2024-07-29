from zootopia.core.schema import ActionType, RoomTableModel, ZootopiaMessage, Task, RespondTask, ReviveTask, Task, MessageTableModel
from config.config import Config, ActionManagerConfig, MemoryManagerConfig, FilterConfig, ConcurrencyManagerConfig
from zootopia.platform.platform import MessageProviderBase
from zootopia.storage.database.supabase import SupabaseDB

from zootopia.core.exceptions import RequestCanceledException
from zootopia.context import BaseContextManager
from zootopia.agent.filter import MessageFilter, FilterInput, FilterResult
from zootopia.agent.action import ActionManager
from zootopia.agent.memory import MemoryManager
from zootopia.server.concurrency import ConcurrencyManager

from zootopia.core.logger import logger
from zootopia.core.utils.utils import get_current_time_readable



class Agent:
    def __init__(
        self, 
        messaging_service: MessageProviderBase,
        database_service: SupabaseDB,
        room: RoomTableModel,
        filter_config: FilterConfig, 
        action_config: ActionManagerConfig, 
        memory_config: MemoryManagerConfig,
        task_config: ConcurrencyManagerConfig,
        agent_prompt: str
    ) -> None:
        self.agent_prompt = agent_prompt
        self.room = room
        self.database_service = database_service
        self.filter = MessageFilter.from_config(filter_config)
        self.action = ActionManager.from_config(action_config, messaging_service)
        self.memory = MemoryManager.from_config(memory_config, database_service, room)
        self.concurrency = ConcurrencyManager.from_config(task_config, room.id)

    @classmethod
    def from_config(cls, config: Config, context: BaseContextManager) -> "Agent":
        return cls(
            messaging_service=context.messaging_service,
            database_service=context.database,
            room=context.room,
            filter_config=config.BEHAVIORS_CONFIG.FILTER,
            action_config=config.BEHAVIORS_CONFIG.ACTION_MANAGER,
            memory_config=config.BEHAVIORS_CONFIG.MEMORY_MANAGER,
            task_config=config.BEHAVIORS_CONFIG.CONCURRENCY_MANAGER,
            agent_prompt=context.agent.prompt
        )

    async def handle_chat_task(self, task: Task) -> bool:
        logger.info(f"🟢 {task}")
        await self.concurrency.start_new()

        try:
            # Get recent messages
            recent_messages = self.memory.get_recent_messages(count=task.recent_message_count)
            
            # If responding to user, store user message
            if isinstance(task, RespondTask):
                self.memory.store_message(MessageTableModel(
                    room_id=self.room.id,
                    from_user=True,
                    content=task.user_message.content
                ))

                possible_actions = [
                    ActionType.MESSAGE,
                    ActionType.RECALL,
                    ActionType.WEB_SEARCH,
                ]

                # TODO: Detect intent of message 
                # - Save event to schedules table and add it to Redis scheduler

                recent_messages.append({"role": "user", "content": task.user_message.content})

            system_prompt_template = """
            {agent_prompt}

            Your task: {instructions}

            It is now {current_time}
            {prompt_addition}
            """

            max_attempts = 2
            prompt_addition = ""

            for attempt in range(max_attempts):
                await self.concurrency.verify_is_latest_request()

                system_prompt = system_prompt_template.format(
                    agent_prompt=self.agent_prompt,
                    instructions=task.instructions,
                    current_time=get_current_time_readable(),
                    prompt_addition=prompt_addition
                )

                logger.info(f"🟢 System prompt (Attempt {attempt + 1}/{max_attempts}):\n{system_prompt}")
                logger.info(f"🟢 Recent messages:\n{recent_messages}")

                response_text = self.action.generate_message(recent_messages, system_prompt)

                filter_result = self.filter.verify(FilterInput(
                    from_user=False,
                    agent_prompt=self.agent_prompt,
                    messages=recent_messages,
                    new_message=response_text
                ))

                logger.info(filter_result.message)

                if filter_result.approved:
                    await self.concurrency.verify_is_latest_request()
                    await self.action.send_message(response_text)
                    self.memory.store_message(MessageTableModel(
                        room_id=self.room.id,
                        from_user=False,
                        content=response_text
                    ))
                    return True
                
                if attempt == max_attempts - 1:
                    logger.warning(f"Max attempts ({max_attempts}) reached. Unable to generate appropriate response.")
                    return False

                # Prepare for next iteration if not approved
                prompt_addition = filter_result.prompt_addition

            return False

        except RequestCanceledException:
            logger.info(f"Request cancelled for room {self.room.id} due to new request")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in processing chat: {str(e)}")
            return False