from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from zootopia.core.schema import MessageTableModel, IntentType
import json
from zootopia.controller.agent.intent import (
    IntentInput,
    IntentOutput,
    IntentResult,
    Confidence,
    IntentProcessor,
    IntentFactory,
)


@dataclass
class SkipIntentInput(IntentInput):
    recent_messages: List[MessageTableModel]

    def __repr__(self) -> str:
        return f"SkipIntentInput(recent_messages_count={len(self.recent_messages)})"


@dataclass
class SkipIntentOutput(IntentOutput):
    should_respond: bool
    reason: str


@dataclass
class SkipIntentResult(IntentResult):
    should_respond: bool
    reason: str

    @property
    def message(self) -> str:
        return f"{'🟢 Should respond' if self.should_respond else '🔴 Should not respond'}: {self.reason}"

    def __repr__(self) -> str:
        return f"SkipIntentResult(should_respond={self.should_respond}, reason='{self.reason[:50]}...')"


@IntentFactory.register(IntentType.SKIP)
class SkipIntent(IntentProcessor[SkipIntentInput, SkipIntentOutput, SkipIntentResult]):
    TEMPLATE: str = """
    Your task is to analyze the given conversation and determine if there's a need for a response.

    Guidelines:
    - Respond if the user asks a question or requests information.
    - Respond if the user expresses a need or concern.
    - Don't respond to simple acknowledgments like "OK", "Alright", or "Got it".
    - Don't respond if the conversation appears to be concluding naturally.
    - Consider the context of recent messages.

    Recent messages:
    {messages}

    Respond in JSON:
    {output_format}
    """

    def process(
        self,
        input: SkipIntentInput,
        max_retries: int = 1,
        confidence_threshold: Optional[Confidence] = None,
    ) -> SkipIntentResult:
        formatted_messages = "\n".join(
            [
                f"{'User' if msg.from_user else 'Assistant'}: {msg.content}"
                for msg in input.recent_messages[
                    -5:
                ] 
            ]
        )

        output_format = json.dumps(
            SkipIntentOutput(
                confidence=Confidence.HIGH, should_respond=True, reason=""
            ).__dict__,
            indent=2,
        )

        system_prompt = self.TEMPLATE.format(
            messages=formatted_messages, output_format=output_format
        )

        response = self._generate_llm_response(
            system_prompt,
            "Analyze the conversation and determine if a response is needed.",
        )
        return self._parse_response(
            response, input.recent_messages, confidence_threshold
        )

    def _parse_response(
        self,
        response: Dict[str, Any],
        analyzed_data: List[MessageTableModel],
        confidence_threshold: Optional[Confidence],
    ) -> SkipIntentResult:
        try:
            output = SkipIntentOutput(**response)
            return SkipIntentResult(
                approved=True,  # The SkipIntent doesn't use the 'approved' field in the same way as other intents
                should_respond=output.should_respond,
                reason=output.reason,
            )
        except (KeyError, ValueError) as e:
            return SkipIntentResult(
                approved=False,
                should_respond=False,
                reason=f"Error parsing LLM response: {str(e)}. Defaulting to not responding.",
            )
