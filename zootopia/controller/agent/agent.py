from zootopia.core.schema import RoomTableModel, MessageTableModel, IntentType
from zootopia.controller.tasks.task_types import (
    BaseTask,
    RespondTask,
)
from zootopia.services import MessageProvider, SupabaseDB
from zootopia.core.exceptions import RequestCanceledException
from zootopia.controller.context import BaseContextManager
from zootopia.controller.agent.intent import (
    FilterIntentInput,
    FilterIntentResult,
    SkipIntentInput,
    SkipIntentResult,
    Confidence,
    IntentConfig,
    IntentConfigManager,
    IntentFactory,
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
        self.action = ActionManager(self.messaging_service)
        self.memory = MemoryManager(self.database_service, self.room)
        default_configs = {
            IntentType.FILTER: IntentConfig(
                message_count=5, confidence_threshold=Confidence.HIGH, enabled=True
            ),
            IntentType.SCHEDULE: IntentConfig(
                message_count=3, confidence_threshold=Confidence.MEDIUM, enabled=True
            ),
            IntentType.SKIP: IntentConfig(
                message_count=3, confidence_threshold=Confidence.HIGH, enabled=True
            ),
        }
        self.intent_config = IntentConfigManager(intent_configs or default_configs)
        self.intent_factory = IntentFactory()

    async def handle_chat_task(self, task: BaseTask) -> bool:
        logger.info(f"🟢 {task}")

        try:
            # Get recent messages
            all_recent_messages = self.memory.get_recent_messages(
                count=task.recent_message_count
            )

            if isinstance(task, RespondTask):
                msg = task.user_message.content

                # If responding to user, store user message
                self.memory.store_message(
                    MessageTableModel(
                        room_id=self.room.id,
                        from_user=True,
                        content=msg,
                    )
                )

                # # Process skip intent
                # # TODO: 
                # if self.intent_config.is_enabled(IntentType.SKIP):
                #     skip_intent = self.intent_factory.create(IntentType.SKIP)
                #     if skip_intent:
                #         skip_messages = self.intent_config.get_past_messages(
                #             IntentType.SKIP, all_recent_messages
                #         )
                #         skip_result: SkipIntentResult = skip_intent.process(
                #             input=SkipIntentInput(
                #                 agent_prompt=self.agent_prompt,
                #                 messages=skip_messages,
                #                 message=msg,
                #             ),
                #             confidence_threshold=self.intent_config.get_confidence_threshold(
                #                 IntentType.SKIP,
                #             ),
                #         )
                #         logger.info(skip_result.message)
                #         if skip_result.approved:
                #             logger.info(
                #                 f"Skipping response due to skip intent: {skip_result.reason}"
                #             )
                #             return True

                # Have agent decide whether to schedule something

                all_recent_messages.append({"role": "user", "content": msg})

            # Create the prompt for the agent message
            system_prompt_template = """
            {agent_prompt}

            Your task: {instructions}

            - Carefully consider the context of recent messages to:
            a) Avoid repeating information already provided.
            b) Identify opportunities to drive the conversation forward, keeping it fresh and lively.

            It is now {current_time}

            Prompt addition: {prompt_addition}
            """

            # Use Filter intent to ensure quality of agent response
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
                    from_user=False,
                    analyzed_message=response_text,
                    approved=True,
                    confidence=Confidence.HIGH,
                    proposed_message="",
                )
            else:
                filter_intent = self.intent_factory.create(IntentType.FILTER)
                if filter_intent:
                    filter_messages = self.intent_config.get_past_messages(
                        IntentType.FILTER, all_recent_messages
                    )
                    filter_result: FilterIntentResult = filter_intent.process(
                        input=FilterIntentInput(
                            from_user=False,
                            agent_prompt=self.agent_prompt,
                            messages=filter_messages,
                            message=response_text,
                        ),
                        confidence_threshold=self.intent_config.get_confidence_threshold(
                            IntentType.FILTER
                        ),
                    )
                else:
                    logger.error("Failed to create FilterIntent")
                    return False

            logger.info(filter_result.message)

            # If approved by filter or if there's a high-confidence proposed message, send and store
            if filter_result.approved:
                final_message = response_text
            elif filter_result.proposed_message:
                final_message = filter_result.proposed_message
            else:
                logger.warning("Unable to generate appropriate response.")
                return False

            await self.action.handle_message_send(final_message)
            self.memory.store_message(
                MessageTableModel(
                    room_id=self.room.id, from_user=False, content=final_message
                )
            )
            return True

        except RequestCanceledException:
            logger.info(f"Request cancelled for room {self.room.id} due to new request")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in processing chat: {str(e)}")
            return False