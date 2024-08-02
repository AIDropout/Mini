from typing import Dict, Any, Optional
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
from datetime import datetime
from zootopia.core.schema import IntentType
from zootopia.utils.utils import EnhancedJSONEncoder


@dataclass
class ScheduleIntentInput(IntentInput):
    text: str

    def __repr__(self) -> str:
        return f"ScheduleIntentInput(text='{self.text[:20]}...')"


@dataclass
class ScheduleIntentOutput(IntentOutput):
    confidence: Confidence
    intent: Optional[str] = None
    name: Optional[str] = None
    run_at: Optional[str] = None


@dataclass
class ScheduleIntentResult(IntentResult):
    from_user: bool
    analyzed_text: str
    approved: bool
    confidence: Confidence
    intent: Optional[str] = None
    name: Optional[str] = None
    run_at: Optional[datetime] = None

    @property
    def message(self) -> str:
        if self.approved:
            return f"🟢 Schedule intent detected: {self.intent} - {self.name} at {self.run_at} (Confidence: {self.confidence})"
        else:
            return f"🔴 No specific schedule intent detected (Confidence: {self.confidence})"

    def __repr__(self) -> str:
        return (
            f"ScheduleIntentResult(from_user={self.from_user}, "
            f"approved={self.approved}, "
            f"confidence={self.confidence.name}, "
            f"intent='{self.intent}', "
            f"name='{self.name}', "
            f"run_at='{self.run_at}')"
        )


@IntentFactory.register(IntentType.SCHEDULE)
class ScheduleIntent(
    IntentProcessor[ScheduleIntentInput, ScheduleIntentOutput, ScheduleIntentResult]
):
    TEMPLATE: str = """
    You are a schedule intent detector for the following text:
    {text}

    Your task is to determine if there's a need to schedule a response or reminder in the future.

    If a scheduling intent is detected, respond with a JSON object containing the following information:
    {{
        "confidence": "HIGH",
        "intent": "schedule",
        "name": "Tell John happy birthday",
        "run_at": "YYYY-MM-DD HH:MM:SS"
    }}

    If no scheduling intent is detected, respond with a JSON object indicating low confidence:
    {{
        "confidence": "LOW"
    }}

    Ensure that the "run_at" field is a valid date and time in the future, formatted as specified.

    Respond in JSON:
    {output_format}
    """

    def process(
        self,
        input: ScheduleIntentInput,
        max_retries: int = 3,
        confidence_threshold: Optional[Confidence] = None,
    ) -> ScheduleIntentResult:
        output_format = json.dumps(
            ScheduleIntentOutput(confidence=Confidence.HIGH).__dict__,
            indent=2,
            cls=EnhancedJSONEncoder,
        )

        system_prompt = self.TEMPLATE.format(
            text=input.text,
            output_format=output_format,
        )

        for attempt in range(max_retries):
            response = self._generate_llm_response(
                system_prompt, "Detect schedule intent."
            )
            result = self._parse_response(response, input.text, confidence_threshold)

            if result.approved:
                return result

            if attempt == max_retries - 1:
                return result

            # If not approved and not the last attempt, update the system prompt
            system_prompt += (
                f"\n\nPrevious attempt failed. Please try again with higher confidence."
            )

        return result  # Return the last result if all attempts fail

    def _parse_response(
        self,
        response: Dict[str, Any],
        analyzed_text: str,
        confidence_threshold: Optional[Confidence],
    ) -> ScheduleIntentResult:
        try:
            output = ScheduleIntentOutput(**response)
            confidence = Confidence[output.confidence.upper()]
            approved = (
                confidence >= (confidence_threshold or Confidence.LOW)
                and output.intent is not None
            )

            return ScheduleIntentResult(
                from_user=False,
                analyzed_text=analyzed_text,
                approved=approved,
                confidence=confidence,
                intent=output.intent,
                name=output.name,
                run_at=(
                    datetime.strptime(output.run_at, "%Y-%m-%d %H:%M:%S")
                    if output.run_at
                    else None
                ),
            )
        except (KeyError, ValueError) as e:
            return ScheduleIntentResult(
                from_user=False,
                analyzed_text=analyzed_text,
                approved=False,
                confidence=Confidence.LOW,
                intent=None,
                name=None,
                run_at=None,
            )
