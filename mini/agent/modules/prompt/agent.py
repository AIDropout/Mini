from typing import Union

from pydantic import BaseModel

from mini.agent.modules.prompt.base import BasePromptModule
from mini.agent.modules.prompt.prompts import AGENT_PROMPT
from mini.core.models.context import Context
from mini.core.models.message_tasks import ProactiveTask, ResponseTask
from mini.database.database import DatabaseManager
from mini.utils.time import TimeManager


class ResponseFormat(BaseModel):
    response: str


class AgentPromptModule(BasePromptModule):
    def __init__(
        self,
        database_manager: DatabaseManager,
        context: Context,
        time_manager: TimeManager,
    ) -> None:
        super().__init__(database_manager, context, time_manager)
        self._return_hint = ResponseFormat(
            response="insert your message here",
        ).model_dump()

    @property
    def response_format(self):
        return ResponseFormat

    def _build_agent_prompt(self) -> str:
        return AGENT_PROMPT.format(
            role=self._role, rules=self._rules, actions=self._actions
        )

    def build_prompt(
        self,
        task: Union[ResponseTask, ProactiveTask],
        relevant_memories: str | None = None,
    ) -> str:
        prompt = []
        agent_prompt = self._build_agent_prompt()
        metadata = self._build_metadata(
            last_agent_message_time=task.context.room.agent_last_msg_sent_at,
            last_user_message_time=task.context.room.last_msg_sent_at,
        )
        return_hint = self._build_return_hint()
        instructions = self._build_additional_instructions(task.instructions)

        # NOTE: ORDER MATTERS IN PROMPTING
        prompt.append(agent_prompt)
        prompt.append(instructions)
        prompt.append(metadata)
        if relevant_memories:
            prompt.append(self._build_memories(relevant_memories))
        prompt.append(return_hint)
        return "\n\n".join(prompt)
