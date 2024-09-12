import json
from typing import Dict, List

from mini.controller.agent.modules.base import AgentModule
from mini.core.schema.tables import Agent, Room, Tables, User
from mini.manager.database import DatabaseManager
from mini.manager.time import TimeManager


class PromptModule(AgentModule):
    def __init__(
        self,
        database_manager: DatabaseManager,
        time_manager: TimeManager,
    ) -> None:
        super().__init__(database_manager)
        self.time_manager = time_manager
        self.database_manager = database_manager

        self.count_messages = self.database_manager.count_rows(
            table_name=Tables.MESSAGES
        )
        self.days_since_last_seen = 0  # TODO

        # set on configure
        self.is_subscribed = False
        self.role: str = ""
        self.rules: list[str] = []
        self.moods: list[str] = []
        self.agent_return_hint = None

    def configure(self, room: Room, agent: Agent, user: User):
        super().configure(room, agent, user)
        self._load_agent_data()

    def _load_agent_data(self) -> None:
        self.role = self.agent.prompt_role
        self.rules = self.agent.prompt_rules
        self.moods = self.agent.prompt_moods

        self.agent_return_hint = {
            "responses": self._response_moods(),
            "best_response": "insert the best response to keep convo flowing, adhearing to user's requests, but keep it unpredictable",
            "reasoning": "short reasoning for picking the best response",
        }

        self.is_subscribed = self.user.is_subscribed

    def _response_moods(self) -> list[str]:
        return [f"insert {mood} message" for mood in self.moods]

    def build_role(self) -> str:
        return self.role

    def build_rules(self) -> str:
        rules = "\n".join([f"- {rule}" for rule in self.rules])
        return f"""
        **RULES:**

        Keep the following in mind:
        {rules}
        """

    def build_metadata(self, relevant_memories: str) -> str:
        return f"""
        **METADATA:**

        - Days since last interaction: {self.days_since_last_seen}
        - Time: {self.time_manager.current_readable_time()}
        - Here are relevant memories:
        {relevant_memories}
        """

    def build_return_hint(self) -> str:
        return f"""
        **RETURN HINT:**

        Ensure you only respond with the following schema (keep it exciting):
        {json.dumps(self.agent_return_hint)}
        """

    def build_chat_history(self, chat_history: List[Dict[str, str]] | None) -> str:
        if chat_history is None:
            return ""

        chat_history = self._prepare_messages(chat_history)
        for chat in chat_history:
            if chat["role"] == "assistant":
                chat["role"] = self.agent.name

        chat_history_str = "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in chat_history]
        )

        return f"""
        **CHAT HISTORY:**
        
        You must respond to the following chat history:
        {chat_history_str}
        """

    def _prepare_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Prepare messages by combining consecutive user messages."""
        prepared = []
        for msg in messages:
            if prepared and prepared[-1]["role"] == msg["role"] == "user":
                prepared[-1]["content"] += f" | {msg['content']}"
            else:
                prepared.append(msg)
        if prepared and prepared[-1]["role"] == "assistant":
            prepared.append({"role": "user", "content": "[ignore]"})
        return prepared

    def build_prompt(
        self, relevant_memories: str, chat_history: List[Dict[str, str]] | None = None
    ) -> str:
        self._load_agent_data()

        prompt = [
            self.build_role(),
            self.build_rules(),
            self.build_metadata(relevant_memories=relevant_memories),
            self.build_chat_history(chat_history),
            self.build_return_hint(),
        ]

        return "\n\n".join(prompt)
