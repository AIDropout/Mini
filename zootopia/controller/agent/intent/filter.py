from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from abc import ABC
from zootopia.services import LLM
from zootopia.core.config import config
import json
from zootopia.controller.agent.intent import (
    IntentInput,
    IntentOutput,
    IntentResult,
    ConfidenceScore,
)


@dataclass
class FilterIntentInput(IntentInput):
    from_user: bool
    agent_prompt: str
    messages: List[Dict[str, str]]
    new_message: str

    def __repr__(self) -> str:
        return (
            f"FilterInput(from_user={self.from_user}, "
            f"new_message='{self.new_message[:20]}...')"
        )


@dataclass
class FilterIntentOutput(IntentOutput):
    approved: bool
    confidence: ConfidenceScore
    prompt_addition: str = ""


@dataclass
class FilterIntentResult(IntentResult):
    from_user: bool
    analyzed_message: str
    approved: bool
    confidence: ConfidenceScore
    prompt_addition: str = ""

    @property
    def message(self) -> str:
        if self.approved:
            return "🟢 LLM response APPROVED by filter"
        else:
            truncated_message = (
                self.analyzed_message[:50] + "..."
                if len(self.analyzed_message) > 50
                else self.analyzed_message
            )
            truncated_addition = (
                self.prompt_addition[:50] + "..."
                if len(self.prompt_addition) > 50
                else self.prompt_addition
            )
            return f"🔴 LLM response [{truncated_message}] FAILED with prompt addition [{truncated_addition}]"

    def __repr__(self) -> str:
        return (
            f"FilterResult(from_user={self.from_user}, "
            f"approved={self.approved}, "
            f"addition='{self.prompt_addition[:50]}...')"
        )


class MessageFilter:
    TEMPLATE: str = """
    You are the following character:
    {agent_prompt}

    You are about to send the following message:
    {new_message}

    Guidelines:
    - Consider the conversation context and agent's role.
    - Your response must be in JSON format.
    - Confidence score should be an integer between 0 and 100.


    Examples of typically inappropriate messages:
    - "I'm sorry I'm not comfortable..."
    - Acknowledging its origins ex. "I am an AI model trained by Anthropic..."
    - If the character is displaying lack of ego and blindly following instructions
    - If it implicitly proves that the agent is an AI or is an AI role playing as a character

    Recent messages: {messages}

    Respond in JSON:
    {output_format}

    This will guide the next LLM iteration. For instance, if the character's response is deemed too silly, it should steer the next LLM's response to be less so. Ensure that the character does not admit to being an AI, acknowledge its training origins, or show lack of ego in future responses.

    """

    def __init__(self):
        self.llm = LLM(config.FILTER_LLM)

    def verify(
        self,
        input: FilterIntentInput,
        max_retries: int = 3,
        confidence_threshold: Optional[ConfidenceScore] = None,
    ) -> FilterIntentResult:
        output_format = json.dumps(
            FilterIntentOutput(approved=True, confidence=ConfidenceScore(100)).__dict__,
            indent=2,
        )

        system_prompt = self.TEMPLATE.format(
            agent_prompt=input.agent_prompt,
            new_message=input.new_message,
            messages=input.messages,
            output_format=output_format,
        )

        for attempt in range(max_retries):
            response = self.llm.generate_response(
                messages=[{"role": "user", "content": "Verify the message."}],
                system_prompt=system_prompt,
                json_mode=True,
            )

            result = self._parse_response(response, input.new_message)
            
            if confidence_threshold is not None:
                if result.approved and result.confidence.is_confident(confidence_threshold) or attempt == max_retries - 1:
                    return result
            else:
                if result.approved or attempt == max_retries - 1:
                    return result

            # If not approved and not the last attempt, update the system prompt
            system_prompt += f"\n\nPrevious attempt failed. Please try again. Error: {result.prompt_addition}"

        return result  # Return the last result if all attempts fail

    def _parse_response(
        self, response: Dict[str, Any], analyzed_message: str
    ) -> FilterIntentResult:
        try:
            response["confidence"] = ConfidenceScore(response["confidence"])
            output = FilterIntentOutput(**response)
            return FilterIntentResult(
                from_user=False,
                analyzed_message=analyzed_message,
                approved=output.approved,
                confidence=output.confidence,
                prompt_addition=output.prompt_addition,
            )
        except (ValueError, TypeError) as e:
            return FilterIntentResult(
                from_user=False,
                analyzed_message=analyzed_message,
                approved=False,
                confidence=ConfidenceScore(0),
                prompt_addition=f"Error parsing filter response: {str(e)}. Please regenerate.",
            )
