from zootopia.core.schema import RoomTableModel, MessageTableModel, IntentType
from zootopia.controller.tasks.task_types import (
    BaseTask,
    RespondTask,
    ReviveTask,
    RemindTask,
)

from zootopia.services import MessageProvider, SupabaseDB
from zootopia.core.exceptions import RequestCanceledException
from zootopia.controller.context import BaseContextManager
from zootopia.controller.agent.intent import (
    MessageFilter,
    FilterIntentInput,
    FilterIntentResult,
    Confidence,
    IntentConfig,
    IntentConfigManager,
)

from zootopia.controller.agent.action import ActionManager
from zootopia.memory import MemoryManager

from zootopia.core.logger import logger
from zootopia.utils.time_utils import get_current_time_readable
from typing import Dict


class Agent:
    def __init__(
        self,
        context: BaseContextManager,
        intent_configs: Dict[str, IntentConfig] = None,
    ) -> None:
        self.messaging_service: MessageProvider = context.messaging_service
        self.database_service: SupabaseDB = context.database
        self.room: RoomTableModel = context.room
        self.agent_prompt: str = context.agent.prompt
        self.filter = MessageFilter()
        self.action = ActionManager(self.messaging_service)
        self.memory = MemoryManager(self.database_service, self.room)
        default_configs = {
            IntentType.FILTER: IntentConfig(
                message_count=5, confidence_threshold=Confidence.HIGH, enabled=True
            ),
            IntentType.SCHEDULE: IntentConfig(
                message_count=7, confidence_threshold=Confidence.MEDIUM, enabled=True
            ),
            IntentType.SKIP: IntentConfig(
                message_count=3, confidence_threshold=Confidence.LOW, enabled=True
            ),
        }
        self.intent_config = IntentConfigManager(intent_configs or default_configs)

    async def handle_chat_task(self, task: BaseTask) -> bool:
        logger.info(f"🟢 {task}")

        try:
            # Get recent messages
            all_recent_messages = self.memory.get_recent_messages(
                count=task.recent_message_count
            )

            # If responding to user, store user message
            if isinstance(task, RespondTask):
                msg = task.user_message.content

                self.memory.store_message(
                    MessageTableModel(
                        room_id=self.room.id,
                        from_user=True,
                        content=msg,
                    )
                )

                # Have agent decide whether it should respond

                # Have agent decide whether to schedule something

                all_recent_messages.append({"role": "user", "content": msg})

            system_prompt_template = """
            {agent_prompt}

            Your task: {instructions}

            It is now {current_time}

            Prompt addition: {prompt_addition}
            """

            # A separate LLM checks to see if LLM response meets criteria
            max_attempts = 2
            prompt_addition = ""

            for attempt in range(max_attempts):

                system_prompt = system_prompt_template.format(
                    agent_prompt=self.agent_prompt,
                    instructions=task.instructions,
                    current_time=get_current_time_readable(),
                    prompt_addition=prompt_addition,
                )

                logger.info(
                    f"🟢 System prompt (Attempt {attempt + 1}/{max_attempts}):\n{system_prompt}"
                )
                logger.info(f"🟢 Recent messages:\n{all_recent_messages}")

                response_text = self.action.generate_message(
                    all_recent_messages, system_prompt
                )

                filter_result = None
                if not self.intent_config.is_enabled(IntentType.FILTER):
                    filter_result = FilterIntentResult(
                        approved=True, message="Filtering disabled"
                    )
                else:
                    filter_messages = self.intent_config.get_past_messages(
                        IntentType.FILTER, all_recent_messages
                    )
                    filter_result: FilterIntentResult = self.filter.verify(
                        input=FilterIntentInput(
                            from_user=False,
                            agent_prompt=self.agent_prompt,
                            messages=filter_messages,
                            new_message=response_text,
                        ),
                        confidence_threshold=self.intent_config.get_confidence_threshold(
                            IntentType.FILTER
                        ),
                    )

                logger.info(filter_result.message)

                # If approved by filter, continue sending and storing
                if filter_result.approved:
                    await self.action.handle_message_send(response_text)
                    self.memory.store_message(
                        MessageTableModel(
                            room_id=self.room.id, from_user=False, content=response_text
                        )
                    )
                    return True

                if attempt == max_attempts - 1:
                    logger.warning(
                        f"Max attempts ({max_attempts}) reached. Unable to generate appropriate response."
                    )
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
