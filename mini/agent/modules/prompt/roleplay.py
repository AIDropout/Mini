from typing import List

from pydantic import BaseModel

from mini.core.models.context import Context
from mini.database.database import DatabaseManager
from mini.agent.modules.prompt.base import BasePromptModule, ChatMessage
from mini.utils.time import TimeManager


class ResponseFormat(BaseModel):
    responses: list[str]
    best_response: str
    reasoning: str


class RoleplayPromptModule(BasePromptModule):
    def __init__(
        self,
        database_manager: DatabaseManager,
        context: Context,
        time_manager: TimeManager
    ) -> None:
        super().__init__(database_manager, context, time_manager)
        self._role = context.agent.prompt_role
        self._rules = context.agent.prompt_rules
        self._moods = context.agent.prompt_moods
        self._return_hint = {}

    @property
    def response_format(self):
        return ResponseFormat

    def _load_roleplay_data(self) -> None:
        response_format = ResponseFormat(
            responses=[
                "set the scene and introduce the character's actions.",
                "move the roleplay forward with character dialogue.",
                "conclude the character's current actions or story arc.",
            ],
            best_response="insert a combination of the best response here",
            reasoning="adjectives describing reasoning for the best response",
        )

        self._return_hint = response_format.model_dump()

    def _build_scenario(self) -> str:
        return """
        **SCENARIO:**

        Create an immersive and dynamic scene for the roleplay.
        Craft a captivating story that adapts to the user's responses and maintains excitement with unexpected twists and engaging elements.
        """

    def _build_character(self) -> str:
        return f"""
        **CHARACTER:**

        Build the story around {self.context.agent.name}, who has the following traits: {", ".join(self._moods)}. 
        Use these traits to develop third-person responses that reflect the character's personality and actions in the scene.
        """

    def _build_rules(self) -> str:
        return """
        **RULES:**

        - Response should be 1 short, consice, and impactful sentence.
        - Use very simple 2nd grade language, suitable for a wide audience.
        - Avoid all dialogue.
        - Ensure to move the roleplay forward.
        """

    def build_prompt(
        self,
        chat_history: List[ChatMessage] | None = None,
        relevant_memories: str | None = None,
    ) -> str:
        self._load_roleplay_data()

        prompt = [
            self._build_scenario(),
            self._build_character(),
            self._build_metadata(relevant_memories=relevant_memories),
            self._build_chat_history(chat_history),
            self._build_rules(),
            self._build_return_hint(),
        ]

        return "\n\n".join(prompt)
