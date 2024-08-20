from zootopia.core.schema.tables import (
    Room,
    Message,
    Schedule,
    Agent,
    User,
    Tables,
)
from zootopia.core.schema.task import TaskType
from zootopia.core.schema.intent import IntentType
from zootopia.controller.task.task_types import RespondTask, RemindTask, ReviveTask
from zootopia.manager.database import DatabaseManager
from zootopia.manager.messaging import MessagingManager
from zootopia.controller.agent.modules.intent import (
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
from zootopia.controller.agent.modules.action import ActionModule
from zootopia.controller.agent.modules.subscribe import SubscribeModule
from zootopia.controller.agent.modules.memory import MemoryModule
from zootopia.core.event_logger import event_logger as el
from zootopia.utils.time_utils import get_current_time_readable
from typing import Dict, Union, Optional
from zootopia.service.base import Service


class AgentService(Service):
    def __init__(
        self,
        database_manager: DatabaseManager,
        action_module: ActionModule,
        memory_module: MemoryModule,
        subscribe_module: SubscribeModule,
        intent_configs: Dict[str, IntentConfig] = None,
    ) -> None:
        super().__init__(database_manager)
        self.agent: Agent = None
        self.user: User = None
        self.room: Room = None
        self.action = action_module
        self.memory = memory_module
        self.subscribe = subscribe_module
        # TODO: properly inject intent configs
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

    def configure(
        self, messaging_manager: MessagingManager, agent: Agent, user: User, room: Room
    ) -> None:
        """Sets room details for the agent and its modules"""

        self.agent = agent
        self.user = user
        self.room = room
        self.memory.configure(room, agent, user)
        self.action.configure(room, agent, user)
        self.subscribe.configure(room, agent, user)
        self.action.set_messaging_manager(messaging_manager)

    async def handle_chat_task(
        self, task: Union[RespondTask, RemindTask, ReviveTask]
    ) -> bool:
        """Core logic for generates and sending message"""

        el.log(f"TASK: {task}")

        try:
            # Handle user message for respond tasks
            if isinstance(task, RespondTask):
                user_message = (
                    task.user_message.content
                )  # Was already inserted into database

                el.log(f"RESPONDING TO: '{user_message}' in Room {task.room_id}")

                # Handle subscribe
                result = await self.subscribe.should_continue_conversation()
                el.log(
                    f"""ROOM SUBSCRIPTION STATUS:
                    Continue conversation: {result.continue_conversation}.
                    Subscribe enabled for agent: {result.subscribe_enabled}.
                    User has subscription for agent: {result.subscription_status}.
                    # of Agent messages in Room: {result.agent_message_count}.
                    Agent free message limit: {result.free_msg_limit}.
                    Subscribe message sent: {result.subscribe_msg_sent}.
                """
                )
                if not result.continue_conversation:
                    return True

                # Process schedule intent
                if self.intent_config.is_enabled(IntentType.SCHEDULE):
                    schedule_intent = self.intent_factory.create(IntentType.SCHEDULE)
                    if schedule_intent:

                        existing_tasks = self.database_manager.get_multiple_rows(
                            table_name=Tables.SCHEDULE,
                            conditions={Tables.SCHEDULE__room_id: self.room.id},
                            order_by=Tables.SCHEDULE__run_at,
                            order_details=False,
                        )

                        el.log(
                            f"Here are the existing scheduled tasks for room {self.room.id}: {existing_tasks}",
                        )

                        schedule_result: ScheduleIntentResult = schedule_intent.process(
                            input=ScheduleIntentInput(
                                message=user_message, existing_tasks=existing_tasks
                            ),
                            confidence_threshold=self.intent_config.get_confidence_threshold(
                                IntentType.SCHEDULE
                            ),
                        )

                        if schedule_result.approved:
                            inserted_task = self.database_manager.insert(
                                table_name=Tables.SCHEDULE,
                                item=Schedule(
                                    room_id=self.room.id,
                                    run_at=schedule_result.run_at,
                                    type=TaskType.REMIND,
                                    task=schedule_result.task,
                                    complete=False,
                                ),
                            )

                            el.log(f"Scheduled a task: {inserted_task}")

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

            system_prompt = system_prompt_template.format(
                agent_prompt=self.agent.prompt,
                instructions=task.instructions,
                current_time=get_current_time_readable(),
            )
            el.log(f"SYSTEM PROMPT FOR AGENT: {system_prompt}")
            el.log(f"RECENT MESSAGES PASSED TO AGENT: {all_recent_messages}")

            # Generate agent message
            response_text = self.action.generate_message(
                all_recent_messages, system_prompt
            )

            el.log(f"MAIN LLM RESPONSE: {response_text}")

            # Use Filter intent to ensure quality of agent response
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
                            agent_prompt=self.agent.prompt,
                            messages=filter_messages,
                            message=response_text,
                        ),
                        confidence_threshold=self.intent_config.get_confidence_threshold(
                            IntentType.FILTER
                        ),
                    )

            el.log(f"{filter_result.message}")

            # If approved by filter or if there's a high-confidence proposed message, send and store
            if filter_result.approved:
                final_message = response_text
            elif filter_result.proposed_message:
                final_message = filter_result.proposed_message
            else:
                return False

            success = await self.action.handle_message_send(final_message)
            el.log(f"BIRD SMS SENT: {success}")

            inserted_message = self.database_manager.insert(
                Tables.MESSAGES,
                Message(
                    room_id=self.room.id,
                    sender_id=self.agent.id,
                    content=final_message,
                    type=task.type,
                    log=el.get_logs(),
                ),
            )

        except Exception as e:
            el.log(f"[FAILURE] Unexpected error in processing chat: {str(e)}")
            return False
