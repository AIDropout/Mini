from typing import List

from pydantic import BaseModel

from mini.agent.modules.prompt.base import BasePromptModule, ChatMessage
from mini.core.models.context import Context
from mini.database.database import DatabaseManager
from mini.utils.time import TimeManager


class ResponseFormat(BaseModel):
    best_response: str


class AgentPromptModule(BasePromptModule):
    def __init__(
        self,
        database_manager: DatabaseManager,
        context: Context,
        time_manager: TimeManager,
    ) -> None:
        super().__init__(database_manager, context, time_manager)
        self._role = context.agent.prompt_role
        self._rules = context.agent.prompt_rules
        self._moods = context.agent.prompt_moods
        self._return_hint = {}

    @property
    def response_format(self):
        return ResponseFormat

    def _load_agent_data(self) -> None:
        response_format = ResponseFormat(
            best_response="insert your best response here, be creative, move the conversation forward, be natural",
        )

        self._return_hint = response_format.model_dump()

    def _response_moods(self) -> list[str]:
        return [f"insert {mood} message" for mood in self._moods]

    def _build_role(self) -> str:
        return self._role

    def _build_rules(self) -> str:
        rules = "\n".join([f"- {rule}" for rule in self._rules])
        return f"""
        **RULES:**

        Keep the following in mind:
        {rules}
        """

    def _build_moods(self) -> str:
        moods = "\n".join(self._response_moods())

        return f"""
        **MOODS:**

        Here is a list of moods you can be in:
        {moods}
        """

    def _build_roleplay(self, roleplay: str | None) -> str:
        if roleplay is None:
            return ""

        return f"""
        **ROLEPLAY:**

        Here is the current roleplay:
        {roleplay}

        - ensure to move the roleplay forward.
        """

    def _build_proactive_prompt(self) -> str:
        return """
        **REMINDER:**

        It has been a while since the user has sent you a message.
        Ensure that you build a message that is not necessarily just a continuation of the previous message.
        Try to strike up a new conversation.
        """

    def build_prompt(
        self,
        chat_history: List[ChatMessage] | None = None,
        relevant_memories: str | None = None,
        roleplay: str | None = None,
        proactive_prompt: bool | None = False,
    ) -> str:
        self._load_agent_data()

        prompt = [
            self._build_role(),
            self._build_rules(),
            self._build_moods(),
            self._build_metadata(relevant_memories=relevant_memories),
            # self._build_chat_history(chat_history),
            self._build_roleplay(roleplay),
            self._build_return_hint(),
        ]

        if proactive_prompt:
            prompt.append(self._build_proactive_prompt())

        return "\n\n".join(prompt)
