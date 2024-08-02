from typing import List, Dict, Any
from dataclasses import dataclass
from zootopia.core.schema import MessageTableModel
from zootopia.services import LLM
from zootopia.core.config import config
import json

@dataclass
class SkipIntentInput:
    recent_messages: List[MessageTableModel]

    def __repr__(self) -> str:
        return f"ShouldRespondInput(recent_messages_count={len(self.recent_messages)})"

@dataclass
class SkipIntentOutput:
    should_respond: bool
    reason: str

@dataclass
class SkipIntentResult:
    should_respond: bool
    reason: str

    @property
    def message(self) -> str:
        return f"{'🟢 Should respond' if self.should_respond else '🔴 Should not respond'}: {self.reason}"

    def __repr__(self) -> str:
        return f"ShouldRespondResult(should_respond={self.should_respond}, reason='{self.reason[:50]}...')"

class SkipIntent:
    TEMPLATE: str = """
    Your task is to analyze the given conversation and determine if there's a need for a response.

    Guidelines:
    - Respond if the user asks a question or requests information.
    - Respond if the user expresses a need or concern.
    - Don't respond to simple acknowledgments like "OK", "Alright", or "Got it".
    - Don't respond if the conversation appears to be concluding naturally.
    - Consider the context of the entire conversation.

    Recent messages:
    {messages}

    Respond in JSON:
    {output_format}
    """

    def __init__(self):
        self.llm = LLM(config.SKIP_LLM)

    def should_respond(self, input: SkipIntentInput) -> SkipIntentResult:
        formatted_messages = "\n".join([
            f"{'User' if msg.from_user else 'Assistant'}: {msg.content}"
            for msg in input.recent_messages[-5:]  # Consider last 5 messages for context
        ])

        output_format = json.dumps(SkipIntentOutput(should_respond=True, reason="").__dict__, indent=2)

        system_prompt = self.TEMPLATE.format(
            messages=formatted_messages,
            output_format=output_format
        )

        response = self.llm.generate_response(
            messages=[{"role": "user", "content": "Analyze the conversation and determine if a response is needed."}],
            system_prompt=system_prompt,
            json_mode=True
        )

        return self._parse_response(response)

    def _parse_response(self, response: Dict[str, Any]) -> SkipIntentResult:
        try:
            output = SkipIntentOutput(**response)
            return SkipIntentResult(
                should_respond=output.should_respond,
                reason=output.reason
            )
        except (ValueError, TypeError) as e:
            return SkipIntentResult(
                should_respond=False,
                reason=f"Error parsing LLM response: {str(e)}. Defaulting to not responding."
            )