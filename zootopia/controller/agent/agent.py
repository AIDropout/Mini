from zootopia.core.schema import (
    RoomTableModel,
    MessageTableModel,
    ScheduleTableModel,
    AgentTableModel,
    UserTableModel,
    Tables,
    TaskType,
    IntentType,
)
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
    ScheduleIntentInput,
    ScheduleIntentResult,
)
from zootopia.controller.agent.action import ActionManager
from zootopia.controller.agent.subscribe import SubscribeManager
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
        self.agent: AgentTableModel = context.agent
        self.user: UserTableModel = context.user
        self.agent_prompt: str = context.agent.prompt
        self.action = ActionManager(self.messaging_service)
        self.memory = MemoryManager(self.database_service, self.room, self.agent)
        self.subscribe_manager = SubscribeManager(
            self.database_service, self.action, self.memory, self.room, self.agent
        )
        default_configs = {
            IntentType.FILTER: IntentConfig(
                message_count=5, confidence_threshold=Confidence.HIGH, enabled=True
            ),
            IntentType.SCHEDULE: IntentConfig(
                message_count=3, confidence_threshold=Confidence.MEDIUM, enabled=False
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
            # Handle user message for respond tasks
            if isinstance(task, RespondTask):
                user_message = task.user_message.content # Was already inserted into database

                if not await self.subscribe_manager.should_continue_conversation():
                    return True

                # Process schedule intent
                if self.intent_config.is_enabled(IntentType.SCHEDULE):
                    schedule_intent = self.intent_factory.create(IntentType.SCHEDULE)
                    if schedule_intent:

                        existing_tasks = self.database_service.get_multiple_rows(
                            table_name="schedule",
                            conditions={"room_id": self.room.id},
                            order_by="run_at",
                            order_desc=False,
                        )

                        logger.info(
                            f"Existing scheduled tasks for room {self.room.id}: {existing_tasks}"
                        )

                        schedule_result: ScheduleIntentResult = schedule_intent.process(
                            input=ScheduleIntentInput(
                                message=user_message, existing_tasks=existing_tasks
                            ),
                            confidence_threshold=self.intent_config.get_confidence_threshold(
                                IntentType.SCHEDULE
                            ),
                        )
                        # print("🍊🍊🍊🍊")
                        # print(schedule_result)

                        if schedule_result.approved:
                            inserted_task = self.database_service.insert(
                                table_name=Tables.SCHEDULE.value,
                                item=ScheduleTableModel(
                                    room_id=self.room.id,
                                    run_at=schedule_result.run_at,
                                    type=TaskType.REMIND.value,
                                    task=schedule_result.task,
                                    complete=False,
                                ),
                            )

                            logger.info(f"Scheduled task: {inserted_task}")

                # all_recent_messages.append({"role": "user", "content": user_message})
            all_recent_messages = self.memory.get_recent_messages(
                count=task.recent_message_count
            )

            # Create the prompt for the agent message
            system_prompt_template = """
            {agent_prompt}

            Your task: {instructions}

            - Carefully consider the context of recent messages to:
            a) Avoid repeating information already provided.
            b) Identify opportunities to drive the conversation forward, keeping it fresh and lively.

            It is now {current_time}
            """

            # Use Filter intent to ensure quality of agent response
            system_prompt = system_prompt_template.format(
                agent_prompt=self.agent_prompt,
                instructions=task.instructions,
                current_time=get_current_time_readable(),
            )

            logger.info(f"🟢 System prompt :\n{system_prompt}")
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
                    room_id=self.room.id, sender_id=self.agent.id, content=final_message
                )
            )
            return True

        except RequestCanceledException:
            logger.info(f"Request cancelled for room {self.room.id} due to new request")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in processing chat: {str(e)}")
            return False
