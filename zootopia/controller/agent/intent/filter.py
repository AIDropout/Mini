from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json
from zootopia.controller.agent.intent import (
    IntentInput,
    IntentOutput,
    IntentResult,
    Confidence,
    IntentProcessor,
    IntentFactory,
)
from zootopia.utils.utils import EnhancedJSONEncoder
from zootopia.core.logger import logger
from zootopia.core.schema import IntentType


@dataclass
class FilterIntentInput(IntentInput):
    from_user: bool
    agent_prompt: str
    messages: List[Dict[str, str]]
    message: str

    def __repr__(self) -> str:
        return f"FilterInput(from_user={self.from_user}, new_message='{self.message[:20]}...')"


@dataclass
class FilterIntentOutput(IntentOutput):
    confidence: Confidence
    prompt_addition: str = ""


@dataclass
class FilterIntentResult(IntentResult):
    from_user: bool
    analyzed_message: str
    approved: bool
    confidence: Confidence
    prompt_addition: str = ""

    @property
    def message(self) -> str:
        if self.approved:
            return f"🟢 LLM response APPROVED by filter (Confidence: {self.confidence})"
        else:
            return f"🔴 LLM response FAILED (Confidence: {self.confidence})"

    def __repr__(self) -> str:
        return f"FilterResult(from_user={self.from_user}, approved={self.approved}, confidence={self.confidence})"

    def __repr__(self) -> str:
        return (
            f"FilterResult(from_user={self.from_user}, "
            f"approved={self.approved}, "
            f"confidence={self.confidence.name}, "
            f"addition='{self.prompt_addition[:50]}...')"
        )


@IntentFactory.register(IntentType.FILTER)
class FilterIntent(
    IntentProcessor[FilterIntentInput, FilterIntentOutput, FilterIntentResult]
):
    TEMPLATE: str = """
    You are quality check for the realisticness of the following character:
    {agent_prompt}

    The character is about to send following message:
    {new_message}

    Your task is simply to approve or disapprove of the message.
    - Confidence level should be one of: LOW, MEDIUM, HIGH.
    - The character's message should be in line with its character prompt.

    Examples of typically inappropriate messages:
    - "I'm sorry I'm not comfortable... I am an AI created by Anthropic"
    - Character acknowledging that it's an AI or LLM model
    - Displaying lack of ego and blindly following instructions
    - Implicitly proving that the agent is an AI or is an AI role playing as a character

    Recent messages: {messages}

    Respond in JSON:
    {output_format}

    This will guide the next LLM iteration. For instance, if the character's response is deemed too silly, it should steer the next LLM's response to be less so.

    """

    def process(
        self,
        input: FilterIntentInput,
        max_retries: int = 3,
        confidence_threshold: Optional[Confidence] = None,
    ) -> FilterIntentResult:
        output_format = json.dumps(
            FilterIntentOutput(confidence="HIGH", prompt_addition="").__dict__,
            indent=2,
            cls=EnhancedJSONEncoder,
        )

        system_prompt = self.TEMPLATE.format(
            agent_prompt=input.agent_prompt,
            new_message=input.message,
            messages=input.messages,
            output_format=output_format,
        )

        for attempt in range(max_retries):
            response = self._generate_llm_response(system_prompt, "Verify the message.")
            result = self._parse_response(response, input.message, confidence_threshold)

            if result.approved:
                return result

            if attempt == max_retries - 1:
                return result

            # If not approved and not the last attempt, update the system prompt
            system_prompt += f"\n\nPrevious attempt failed. Please try again with this in mind: {result.prompt_addition}"

        return result  # Return the last result if all attempts fail

    def _parse_response(
        self,
        response: Dict[str, Any],
        analyzed_message: str,
        confidence_threshold: Optional[Confidence],
    ) -> FilterIntentResult:
        try:
            output = FilterIntentOutput(**response)
            confidence = Confidence[output.confidence.upper()]
            approved = confidence >= (confidence_threshold or Confidence.LOW)

            return FilterIntentResult(
                from_user=False,
                analyzed_message=analyzed_message,
                approved=approved,
                confidence=confidence,
                prompt_addition=output.prompt_addition,
            )
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing filter response: {str(e)}")
            return FilterIntentResult(
                from_user=False,
                analyzed_message=analyzed_message,
                approved=False,
                confidence=Confidence.LOW,
                prompt_addition=f"Error parsing filter response: {str(e)}. Please regenerate.",
            )
