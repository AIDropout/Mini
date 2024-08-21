from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from zootopia.core.schema.intent import IntentType
import json
from zootopia.controller.agent.modules.intent.intent_processor import (
    IntentInput,
    IntentOutput,
    IntentResult,
    Confidence,
    IntentProcessor,
)
from zootopia.core.exceptions import LLMResponseParsingError
from zootopia.core.logger import logger
# from zootopia.utils.utils import EnhancedJSONEncoder


@dataclass
class SkipIntentInput(IntentInput):
    agent_prompt: str
    messages: List[Dict[str, str]]


@dataclass
class SkipIntentOutput(IntentOutput):
    # Inherits confidence and reason from IntentOutput
    pass


@dataclass
class SkipIntentResult(IntentResult):
    confidence: Confidence

    @property
    def message(self) -> str:
        return f"{'🟢 Should respond' if self.approved else '🔴 Should not respond'}: {self.reason}"

    def __repr__(self) -> str:
        return f"SkipIntentResult(approved={self.approved}, reason='{self.reason[:50]}...')"


class SkipIntent():
    TEMPLATE: str = """
    Your task is to analyze the given conversation and determine if there's a need for a response.

    Guidelines:
    - Generally, err on the side of responding to maintain engagement.
    - Confidence level should be one of: LOW, MEDIUM, HIGH.
    - Respond to most messages, including brief or simple ones, unless doing so would be redundant or repetitive.
    - Consider skipping a response if:
      1. The message is a very short acknowledgment (e.g., just "OK" or "Got it") AND responding would not add value.
      2. Responding would merely repeat information already given without adding anything new.
      3. The conversation is clearly and definitively concluding (e.g., "Goodbye, thank you for your help").
 
    Agent prompt:
    {agent_prompt}

    Recent messages:
    {messages}

    New message to analyze:
    {new_message}

    Respond in JSON:
    {output_format}
    """

    def process(
        self,
        input: SkipIntentInput,
        max_retries: int = 1,
        confidence_threshold: Optional[Confidence] = None,
    ) -> SkipIntentResult:
        output_format = json.dumps(
            SkipIntentOutput(confidence=Confidence.HIGH, reason="").__dict__,
            indent=2,
            # cls=EnhancedJSONEncoder,
        )

        system_prompt = self.TEMPLATE.format(
            agent_prompt=input.agent_prompt,
            new_message=input.message,
            messages=input.messages,
            output_format=output_format,
        )

        response = self._generate_llm_response(
            system_prompt,
            "Analyze the conversation and determine if a response is needed.",
        )
        return self._parse_response(response, input.message, confidence_threshold)

    def _parse_response(
        self,
        response: Dict[str, Any],
        analyzed_message: str,
        confidence_threshold: Optional[Confidence],
    ) -> SkipIntentResult:
        try:
            output = SkipIntentOutput(**response)
            confidence = Confidence[output.confidence.upper()]
            approved = confidence >= (confidence_threshold or Confidence.LOW)

            return SkipIntentResult(
                analyzed_message=analyzed_message,
                approved=approved,
                confidence=confidence,
                reason=output.reason,
            )
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing skip intent response: {str(e)}")
            raise LLMResponseParsingError()
