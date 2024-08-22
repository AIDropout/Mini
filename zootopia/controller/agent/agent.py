from typing import Union
from zootopia.service.base import Service
from zootopia.controller.agent.modules.intent.filter import FilterModule
from zootopia.controller.agent.modules.action import ActionModule
from zootopia.controller.agent.modules.subscribe import SubscribeModule
from zootopia.controller.agent.modules.memory import MemoryModule
from zootopia.manager.database import DatabaseManager
from zootopia.manager.messaging import MessagingManager
from zootopia.core.event_logger import event_logger as el
from zootopia.controller.task.task_types import RespondTask, RemindTask, ReviveTask
from zootopia.core.schema.tables import Room, Message, Schedule, Agent, User, Tables
from zootopia.utils.time_utils import get_current_time_readable
from zootopia.core.logger import get_logger


class AgentService(Service):
    def __init__(
        self,
        database_manager: DatabaseManager,
        action_module: ActionModule,
        memory_module: MemoryModule,
        subscribe_module: SubscribeModule,
        filter_module: FilterModule,
    ) -> None:
        super().__init__(database_manager)
        self.logger = get_logger(__name__)
        self.agent: Agent = None
        self.user: User = None
        self.room: Room = None
        self.action = action_module
        self.memory = memory_module
        self.subscribe = subscribe_module
        self.filter = filter_module

    def configure(
        self, messaging_manager: MessagingManager, agent: Agent, user: User, room: Room
    ) -> None:
        """Sets room details for the agent and its modules"""

        self.agent = agent
        self.user = user
        self.room = room
        self.memory.configure(room, agent, user)
        self.filter.configure(room, agent, user)
        self.subscribe.configure(room, agent, user)
        self.action.configure(room, agent, user)
        self.action.set_messaging_manager(messaging_manager)

    async def handle_chat_task(
        self, task: Union[RespondTask, RemindTask, ReviveTask]
    ) -> bool:
        """Core logic for generates and sending message"""

        el.log(f"TASK: {task}")

        try:
            if isinstance(task, RespondTask):

                el.log(
                    f"RESPONDING TO: '{task.user_message.content}' in Room {task.room_id}"
                )

                result = await self.subscribe.should_continue_conversation()
                self.logger.info(f"Room subscription status: {repr(result)}")

                if not result.continue_conversation:
                    return True

            all_recent_messages = self.memory.get_recent_messages(
                count=task.recent_message_count
            )
            el.log(f"RECENT MESSAGES PASSED TO AGENT: {all_recent_messages}")

            system_prompt = self._generate_system_prompt(task.instructions)
            el.log(f"SYSTEM PROMPT FOR AGENT: {system_prompt}")

            response_text = self.action.generate_message(
                all_recent_messages, system_prompt
            )
            el.log(f"MAIN LLM RESPONSE: {response_text}")

            final_message = self.filter.process_message(
                all_recent_messages, response_text
            )

            success = await self.action.handle_message_send(final_message)
            el.log(f"BIRD SMS SENT: {success}")

            inserted_message = self._insert_message(task, final_message)

        except Exception as e:
            el.log(f"[FAILURE] Unexpected error in processing chat: {str(e)}")
            return False

    def _generate_system_prompt(self, instructions: str) -> str:
        return f"""
        {self.agent.prompt}

        Your task: {instructions}

        - Carefully consider the context of recent messages to:
        a) Avoid repeating information already provided.
        b) Identify opportunities to drive the conversation forward, keeping it fresh and lively.

        It is now {get_current_time_readable()}
        """

    def _insert_message(
        self, task: Union[RespondTask, RemindTask, ReviveTask], content: str
    ) -> Message:
        """Inserts the agent message"""

        return self.database_manager.insert(
            Tables.MESSAGES,
            Message(
                room_id=self.room.id,
                sender_id=self.agent.id,
                content=content,
                type=task.type,
                log=el.get_logs(),
            ),
        )
