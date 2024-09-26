import json
from typing import Union, Callable

from mini.agent.modules.sender import MessageSenderModule
from mini.agent.modules.filter.filter import MessageFilterModule
from mini.agent.modules.memory.service import MemoryModule
from mini.agent.modules.proactive.schedule_dispatch import ScheduleDispatch
from mini.agent.modules.prompt import (
    AgentPromptModule,
    BasePromptModule,
    ChatMessage,
    RoleplayPromptModule,
)
from mini.core.event_logger import event_logger as el
from mini.core.logger import get_logger
from mini.messaging.tasks.models import ProactiveTask, ResponseTask
from mini.database.database import DatabaseManager

logger = get_logger(__name__)


class AgentService:
    def __init__(
        self,
        database_manager: DatabaseManager,
        schedule_dispatch: ScheduleDispatch,
        message_sender_module: MessageSenderModule,
        memory_module: MemoryModule,
        filter_module: MessageFilterModule,
        prompt_module: BasePromptModule,
        agent_prompt_module: AgentPromptModule,
        role_prompt_module: RoleplayPromptModule,
    ) -> None:
        self.database_manager = database_manager
        self.schedule_dispatch = schedule_dispatch
        self.message_sender = message_sender_module
        self.memory = memory_module
        self.filter = filter_module
        self.agent_prompt = agent_prompt_module
        self.roleplay_prompt = role_prompt_module

    def process_message_task(
        self,
        task: Union[ResponseTask, ProactiveTask],
        check_cancellation: Callable[[], None],
    ) -> bool:
        """Processes a chat task"""
        self.message_sender.set_messaging_provider(task.messaging_provider)

        check_cancellation()

        response, roleplay = self._generate_response(task, check_cancellation)

        text_response = f"**{roleplay}**\n\n{response}" if roleplay else response

        check_cancellation()

        self.message_sender.send_message(text=text_response)

        self._update_proactive_message_schedule()

        return True

    def _generate_response(
        self,
        task: Union[ResponseTask, ProactiveTask],
        check_cancellation: Callable[[], None],
    ) -> tuple[str, str]:

        el.log(f"RECENT MESSAGES PASSED TO AGENT: {task.recent_messages}")

        chat_history = [
            ChatMessage(role=msg["role"], content=msg["content"])
            for msg in task.recent_messages
        ]

        # ROLEPLAY MESSAGE
        roleplay_response = ""
        if task.context.agent.allow_roleplay:
            roleplay_system_prompt = self.roleplay_prompt.build_prompt(
                relevant_memories="", chat_history=chat_history
            )
            el.log(f"SYSTEM PROMPT FOR ROLEPLAY: {roleplay_system_prompt}")

            check_cancellation()

            roleplay_response_text = self.message_sender.generate_message(
                [], roleplay_system_prompt, self.roleplay_prompt.response_format
            )
            el.log(f"ROLEPLAY LLM RESPONSE: {roleplay_response_text}")
            roleplay_response = json.loads(roleplay_response_text).get(
                "best_response", ""
            )

        # AGENT MESSAGE
        agent_system_prompt = self.agent_prompt.build_prompt(
            relevant_memories="",
            chat_history=chat_history,
            roleplay=roleplay_response,
            proactive_prompt=isinstance(task, ProactiveTask),
        )
        el.log(f"SYSTEM PROMPT FOR AGENT: {agent_system_prompt}")

        check_cancellation()

        agent_response_text = self.message_sender.generate_message(
            [], agent_system_prompt, self.agent_prompt.response_format
        )
        el.log(f"AGENT LLM RESPONSE: {agent_response_text}")

        response = json.loads(agent_response_text).get("best_response", "")

        check_cancellation()

        return (
            self.filter.validate_message(task.recent_messages, response),
            roleplay_response,
        )

    def _update_proactive_message_schedule(self):
        self.schedule_dispatch.schedule_proactive_message()
