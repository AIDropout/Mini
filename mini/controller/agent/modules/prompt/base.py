import json
from typing import List, Optional

from pydantic import BaseModel, Field

from mini.controller.agent.modules.base import AgentModule
from mini.core.schema.tables import Agent, Room, User
from mini.storage.database import DatabaseManager
from mini.manager.time import TimeManager


class ChatMessage(BaseModel):
    role: str = Field(
        ..., description="The role of the message sender (e.g., 'user', 'assistant')"
    )
    content: str = Field(..., description="The content of the message")


class BasePromptModule(AgentModule):
    def __init__(
        self,
        database_manager: DatabaseManager,
        time_manager: TimeManager,
    ) -> None:
        super().__init__(database_manager)
        self.time_manager = time_manager
        self.database_manager = database_manager

        self._role = "not set yet"
        self._rules = "not set yet"
        self._moods = ["not set yet"]
        self._is_subscribed = "not set yet"
        self._return_hint = {}

    def configure(self, room: Room, agent: Agent, user: User):
        super().configure(room, agent, user)
        self._load_data()

    def _load_data(self) -> None:
        self._role = self.agent.prompt_role
        self._rules = self.agent.prompt_rules
        self._moods = self.agent.prompt_moods
        self._is_subscribed = self.user.is_subscribed

    def build_prompt(
        self,
        chat_history: Optional[List[ChatMessage]] = None,
        relevant_memories: Optional[str] = None,
    ) -> str:
        raise NotImplementedError("Subclasses must implement build_prompt")

    @property
    def response_format(self) -> BaseModel:
        """The response format of the prompt module."""
        raise NotImplementedError("Subclasses must implement response_format")

    def _prepare_messages(self, chat_history: List[ChatMessage]) -> List[ChatMessage]:
        """Prepare messages by combining consecutive user messages."""
        prepared: List[ChatMessage] = []
        for msg in chat_history:
            if msg.role == "assistant":
                msg.role = self.agent.name
            if prepared and prepared[-1].role == msg.role == "user":
                prepared[-1].content += f" | {msg.content}"
            else:
                prepared.append(msg)
        if prepared and prepared[-1].role == "assistant":
            prepared.append(ChatMessage(role="user", content="[ignore]"))
        return prepared

    def _build_chat_history(self, chat_history: Optional[List[ChatMessage]]) -> str:
        if chat_history is None:
            return ""

        prepared_history = self._prepare_messages(chat_history)
        chat_history_str = "\n".join(
            [f"{msg.role}: {msg.content}" for msg in prepared_history]
        )

        return f"""
        **CHAT HISTORY:**
        
        You must respond to the following chat history:
        {chat_history_str}
        """

    def _build_metadata(self, relevant_memories: str | None = None) -> str:
        memories = (
            f"\n- Here are relevant memories: \n{relevant_memories}"
            if relevant_memories
            else ""
        )

        return f"""
        **METADATA:**

        - Time: {self.time_manager.current_readable_time()}{memories}
        """

    def _build_return_hint(self) -> str:
        return f"""
        **RETURN HINT:**

        Ensure you only respond with the following schema:
        {json.dumps(self._return_hint)}
        """
