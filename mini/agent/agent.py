import json
from typing import Callable, Union

from mini.agent.modules.filter.filter import MessageFilterModule
from mini.agent.modules.memory.service import MemoryModule
from mini.agent.modules.proactive.schedule_dispatch import ScheduleDispatch
from mini.agent.modules.prompt import AgentPromptModule
from mini.agent.modules.sender import MessageSenderModule
from mini.core.event_logger import event_logger as el
from mini.core.logger import get_logger
from mini.core.models.message_tasks import ProactiveTask, ResponseTask

logger = get_logger(__name__)


class AgentService:
    def __init__(
        self,
        schedule_dispatch: ScheduleDispatch,
        message_sender_module: MessageSenderModule,
        memory_module: MemoryModule,
        filter_module: MessageFilterModule,
        agent_prompt_module: AgentPromptModule,
    ) -> None:
        self.schedule_dispatch = schedule_dispatch
        self.message_sender = message_sender_module
        self.memory = memory_module
        self.filter = filter_module
        self.agent_prompt = agent_prompt_module

    def process_message_task(
        self,
        task: Union[ResponseTask, ProactiveTask],
        check_cancellation: Callable[[], None],
    ) -> bool:
        """Processes a chat task"""
        self.message_sender.set_messaging_provider(task.messaging_provider)
        check_cancellation()

        agent_response = self._generate_response(task)
        check_cancellation()

        self.message_sender.send_message(text=agent_response)
        self._update_proactive_message_schedule()
        return True

    def _generate_response(
        self,
        task: Union[ResponseTask, ProactiveTask],
    ) -> str:
        el.log(f"RECENT MESSAGES PASSED TO AGENT: {task.recent_messages}")

        # AGENT PROMPT BUILDING
        agent_system_prompt = self.agent_prompt.build_prompt(
            task=task, relevant_memories=""
        )
        el.log(f"SYSTEM PROMPT FOR AGENT: {agent_system_prompt}")

        # AGENT RESPONSE BUILDING
        agent_response_text = self.message_sender.generate_message(
            task.recent_messages, agent_system_prompt, self.agent_prompt.response_format
        )
        el.log(f"AGENT LLM RESPONSE: {agent_response_text}")

        try:
            agent_response_json = json.loads(agent_response_text)
        except json.JSONDecodeError:
            agent_response_json = {
                "response": agent_response_text
            }  # dangerous, hope filter figures this out if there are issues
        agent_response = self.agent_prompt.response_format(**agent_response_json)
        return self.filter.validate_message(
            task.recent_messages, agent_response.response
        )

    def _update_proactive_message_schedule(self):
        self.schedule_dispatch.schedule_proactive_message()
