from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pydantic import BaseModel, Field
from zootopia.services import LLM
from zootopia.core.config import config
import json

@dataclass
class FilterInput:
    from_user: bool
    agent_prompt: str
    messages: List[Dict[str, str]]
    new_message: str

    def __repr__(self) -> str:
        return (f"FilterInput(from_user={self.from_user}, "
                f"new_message='{self.new_message[:20]}...')")

class FilterOutput(BaseModel):
    approved: bool
    prompt_addition: str = Field(default="")

@dataclass
class FilterResult:
    from_user: bool
    analyzed_message: str
    approved: bool
    prompt_addition: str = ""

    @property
    def message(self) -> str:
        if self.approved:
            return "🟢 LLM response APPROVED by filter"
        else:
            truncated_message = self.analyzed_message[:50] + "..." if len(self.analyzed_message) > 50 else self.analyzed_message
            truncated_addition = self.prompt_addition[:50] + "..." if len(self.prompt_addition) > 50 else self.prompt_addition
            return f"🔴 LLM response [{truncated_message}] FAILED with prompt addition [{truncated_addition}]"

    def __repr__(self) -> str:
        return (f"FilterResult(from_user={self.from_user}, "
                f"approved={self.approved}, "
                f"addition='{self.prompt_addition[:50]}...')")

class MessageFilter:
    TEMPLATE: str = """
    You are the following character:
    {agent_prompt}

    You are about to send the following message:
    {new_message}

    Guidelines:
    - Consider the conversation context and agent's role.
    - Your response must be in JSON format.

    Examples of typically inappropriate messages:
    - "I'm sorry I'm not comfortable..."
    - Acknowledging its origins ex. "I am an AI model trained by Anthropic..."
    - If the character is displaying lack of ego and blindly following instructions
    - If it implicitly proves that the agent is an AI or is an AI role playing as a character

    Recent messages: {messages}

    Respond in JSON:
    {output_format}
    """

    def __init__(self):
        self.llm = LLM(config.FILTER_LLM)

    def verify(self, input: FilterInput) -> FilterResult:
        output_format = json.dumps(FilterOutput.model_json_schema(), indent=2)
        
        system_prompt = self.TEMPLATE.format(
            agent_prompt=input.agent_prompt,
            new_message=input.new_message,
            messages=input.messages,
            output_format=output_format
        )

        response = self.llm.generate_response(
            messages=[{"role": "user", "content": "Verify the message."}],
            system_prompt=system_prompt,
            json_mode=True
        )

        return self._parse_response(response, input.new_message)

    def _parse_response(self, response: Dict[str, Any], analyzed_message: str) -> FilterResult:
        try:
            output = FilterOutput(**response)
            return FilterResult(
                from_user=False,
                analyzed_message=analyzed_message,
                approved=output.approved,
                prompt_addition=output.prompt_addition
            )
        except ValueError as e:
            return FilterResult(
                from_user=False,
                analyzed_message=analyzed_message,
                approved=False,
                prompt_addition=f"Error parsing filter response: {str(e)}. Please regenerate."
            )

# Usage example
def main():
    filter_input = FilterInput(
        from_user=False,
        agent_prompt="You are a helpful assistant.",
        messages=[
            {"role": "user", "content": "Hello, who are you?"},
            {"role": "assistant", "content": "I'm a helpful assistant. How can I assist you today?"}
        ],
        new_message="I'm an AI language model created by Anthropic."
    )

    message_filter = MessageFilter()
    result = message_filter.verify(filter_input)
    print(result.message)

if __name__ == "__main__":
    main()