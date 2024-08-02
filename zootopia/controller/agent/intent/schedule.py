from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from zootopia.services import LLM
from zootopia.core.config import config
import json
from zootopia.controller.agent.intent import IntentInput, IntentOutput, IntentResult
from datetime import datetime

@dataclass
class ScheduleIntentInput(IntentInput):
    text: str

    def __repr__(self) -> str:
        return f"IntentInput(text='{self.text[:20]}...')"

@dataclass
class ScheduleIntentOutput(IntentOutput):
    intent: Optional[str] = None
    name: Optional[str] = None
    run_at: Optional[str] = None

@dataclass
class ScheduleIntentResult(IntentResult):
    original_text: str
    intent: Optional[str] = None
    name: Optional[str] = None
    run_at: Optional[datetime] = None

    @property
    def message(self) -> str:
        if self.intent:
            return f"🟢 Intent detected: {self.intent} - {self.name} at {self.run_at}"
        else:
            return "🔴 No specific intent detected"

    def __repr__(self) -> str:
        return f"IntentResult(intent='{self.intent}', name='{self.name}', run_at='{self.run_at}')"

class Scheduler:
    TEMPLATE: str = """
    Your task is to analyze the given text and determine if there's a need to schedule a response or reminder in the future.

    If a scheduling intent is detected, respond with a JSON object containing the following information:
    {{
        "intent": "schedule",
        "name": "Tell John happy birthday",
        "run_at": "YYYY-MM-DD HH:MM:SS"
    }}

    If no scheduling intent is detected, respond with an empty JSON object:
    {{}}

    Ensure that the "run_at" field is a valid date and time in the future, formatted as specified.

    Example:
    User input: "Remind me to call John tomorrow at 2 PM"
    Response:
    {{
        "intent": "schedule",
        "name": "Call John",
        "run_at": "2024-08-01 14:00:00"
    }}

    Only include the JSON object in your response, without any additional text.

    User input: {text}

    Respond in JSON:
    {output_format}
    """

    def __init__(self):
        self.llm = LLM(config.INTENT_LLM)

    def detect_intent(self, input: ScheduleIntentInput, max_retries: int = 3) -> ScheduleIntentResult:
        output_format = json.dumps(asdict(ScheduleIntentOutput()), indent=2)
        
        system_prompt = self.TEMPLATE.format(
            text=input.text,
            output_format=output_format
        )

        for attempt in range(max_retries):
            response_dict = self.llm.generate_response(
                messages=[{"role": "user", "content": "Detect intent."}],
                system_prompt=system_prompt,
                json_mode=True,
            )

            result = self._parse_response(response_dict, input.text)
            if result.intent or attempt == max_retries - 1:
                return result

            # If no intent detected and not the last attempt, update the system prompt
            system_prompt += f"\n\nPrevious attempt failed to detect an intent. Please try again."

        return result  # Return the last result if all attempts fail

    def _parse_response(self, response: Dict[str, Any], original_text: str) -> ScheduleIntentResult:
        try:
            output = ScheduleIntentOutput(**response)
            return ScheduleIntentResult(
                original_text=original_text,
                intent=output.intent,
                name=output.name,
                run_at=datetime.strptime(output.run_at, "%Y-%m-%d %H:%M:%S") if output.run_at else None
            )
        except (ValueError, TypeError) as e:
            return ScheduleIntentResult(
                original_text=original_text,
                intent=None,
                name=None,
                run_at=None
            )