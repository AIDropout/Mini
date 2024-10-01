import json
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from mini.agent.modules.base import AgentModule
from mini.agent.modules.prompt.prompts import (
    ADDITIONAL_INSTRUCTIONS,
    MEMORIES,
    METADATA,
    RETURN_HINT,
)
from mini.core.models.context import Context
from mini.database.database import DatabaseManager
from mini.utils.time import TimeManager


class BasePromptModule(AgentModule):
    def __init__(
        self,
        database_manager: DatabaseManager,
        context: Context,
        time_manager: TimeManager,
    ) -> None:
        super().__init__(database_manager, context)
        self.time_manager = time_manager
        self._role = context.agent.prompt_role
        self._rules = context.agent.prompt_rules
        self._actions = context.agent.prompt_actions
        self._return_hint = {}

    def build_prompt(self) -> str:
        raise NotImplementedError("Subclasses must implement build_prompt")

    @property
    def response_format(self) -> BaseModel:
        """The response format of the prompt module."""
        raise NotImplementedError("Subclasses must implement response_format")

    def _build_memories(
        self,
        relevant_memories: str | None = None,
    ) -> str:
        return MEMORIES.format(memories=relevant_memories or "")

    def _build_metadata(
        self,
        last_user_message_time: datetime | None = None,
        last_agent_message_time: datetime | None = None,
    ) -> str:
        since_user_msg = None
        since_agent_msg = None
        now = self.time_manager.get_user_datetime()

        if last_user_message_time:
            since_user_msg = self.time_manager.timedelta_to_description(
                now - last_user_message_time
            )

        if last_agent_message_time:
            since_agent_msg = self.time_manager.timedelta_to_description(
                now - last_agent_message_time
            )

        return METADATA.format(
            current_time=self.time_manager.current_readable_time(),
            since_user_msg=since_user_msg or "irrelevant",
            since_agent_msg=since_agent_msg or "irrelevant",
        )

    def _build_additional_instructions(self, additional_instructions: str) -> str:
        return ADDITIONAL_INSTRUCTIONS.format(
            additional_instructions=additional_instructions
        )

    def _build_return_hint(self) -> str:
        return RETURN_HINT.format(json_schema=json.dumps(self._return_hint, indent=2))
