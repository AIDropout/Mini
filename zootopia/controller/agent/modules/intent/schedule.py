from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import json
from zootopia.controller.agent.modules.intent.intent import (
    IntentInput,
    IntentOutput,
    IntentResult,
    Confidence,
    IntentProcessor,
    IntentFactory,
)
from datetime import datetime
from zootopia.core.schema import IntentType, Schedule
from zootopia.utils.utils import EnhancedJSONEncoder
from zootopia.utils.time_utils import get_current_time_cst_iso8601


@dataclass
class ScheduleIntentInput(IntentInput):
    existing_tasks: List[Schedule]

    def __repr__(self) -> str:
        return f"ScheduleIntentInput(text='{self.message[:20]}...')"


@dataclass
class ScheduleIntentOutput(IntentOutput):
    confidence: Confidence
    task: Optional[str] = None
    run_at: str = None


@dataclass
class ScheduleIntentResult(IntentResult):
    analyzed_text: str
    confidence: Confidence
    task: Optional[str] = None
    run_at: str = None

    @property
    def message(self) -> str:
        if self.approved:
            return f"🟢 Schedule intent detected: {self.task} at {self.run_at} (Confidence: {self.confidence})"
        else:
            return f"🔴 No specific schedule intent detected (Confidence: {self.confidence})"

    def __repr__(self) -> str:
        return (
            f"ScheduleIntentResult( "
            f"approved={self.approved}, "
            f"confidence={self.confidence.name}, "
            f"task='{self.task}', "
            f"run_at='{self.run_at}')"
        )


@IntentFactory.register(IntentType.SCHEDULE)
class ScheduleIntent(
    IntentProcessor[ScheduleIntentInput, ScheduleIntentOutput, ScheduleIntentResult]
):
    TEMPLATE: str = """
    You are texting someone who just sent the following text:
    {message}

    Keep track of these you must do in the future. Here are the existing tasks.

    {existing_scheduled_tasks}

    Respond with a JSON object containing the following information:
    {{
        "confidence": "HIGH",
        "task": "John said his birthday is tomorrow. I should tell John happy birthday tomorrow morning",
        "run_at": "YYYY-MM-DDTHH:MM:SS.sss±HH:MM"
    }}

    If no scheduling intent is detected, respond with a JSON object indicating low confidence:
    {{
        "confidence": "LOW"
    }}

    IMPORTANT: For the "run_at" field, you MUST convert any natural language time expressions (e.g. "next Friday at 3pm", "tomorrow morning", "in 2 weeks") into this precise timestamptz format (2024-08-02 16:14:02.295+00). Use the current date and time as reference, and assume the user's local timezone unless otherwise specified. Always ensure the timestamp is in the future.

    Respond in JSON:
    {output_format}

    The time is now {current_time}
    """

    def process(
        self,
        input: ScheduleIntentInput,
        max_retries: int = 1,
        confidence_threshold: Optional[Confidence] = None,
    ) -> ScheduleIntentResult:
        output_format = json.dumps(
            ScheduleIntentOutput(confidence=Confidence.HIGH).__dict__,
            indent=2,
            cls=EnhancedJSONEncoder,
        )

        system_prompt = self.TEMPLATE.format(
            message=input.message,
            existing_scheduled_tasks=input.existing_tasks,
            output_format=output_format,
            current_time=get_current_time_cst_iso8601(),
        )

        for attempt in range(max_retries):
            response = self._generate_llm_response(
                system_prompt, "Detect schedule intent."
            )
            result = self._parse_response(response, input.message, confidence_threshold)

            if result.approved:
                return result

            if attempt == max_retries - 1:
                return result

            system_prompt += (
                "\n\nPrevious attempt failed. Please try again with higher confidence."
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
                and output.task is not None
            )

            return ScheduleIntentResult(
                approved=approved,
                analyzed_text=analyzed_text,
                confidence=confidence,
                task=output.task,
                run_at=output.run_at,
            )

        except (KeyError, ValueError) as e:
            return ScheduleIntentResult(
                approved=False,
                analyzed_text=analyzed_text,
                confidence=Confidence.LOW,
                task=None,
                run_at=None,
            )
