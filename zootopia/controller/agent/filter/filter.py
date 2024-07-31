from typing import List, Dict
from dataclasses import dataclass
from zootopia.services import LLM
from typing import ClassVar
import json
from zootopia.core.config import config

@dataclass
class FilterInput():
    from_user: bool
    agent_prompt: str
    messages: List[Dict[str, str]]
    new_message: str

    def __repr__(self) -> str:
        return (f"FilterInput(from_user={self.from_user}, "
                f"new_message='{self.new_message[:20]}...')")

@dataclass
class FilterResult:
    from_user: bool
    new_message: str
    approved: bool
    prompt_addition: str = ""

    @property
    def message(self) -> str:
        if self.approved:
            return f"🟢 LLM response APPROVED by filter"
        else:
            truncated_message = self.new_message[:50] + "..." if len(self.new_message) > 50 else self.new_message
            truncated_addition = self.prompt_addition[:50] + "..." if len(self.prompt_addition) > 50 else self.prompt_addition
            return f"🔴 LLM response [{truncated_message}] FAILED with prompt addition [{truncated_addition}]"
        
        
    def __repr__(self) -> str:
        return (f"FilterResult(from_user={self.from_user}, "
                f"approved={self.approved}, "
                f"addition='{self.prompt_addition[:50]}...')") 
    

class MessageFilter:
    def __init__(self):
        self.llm = LLM(config.FILTER_LLM)

    def verify(self, input: FilterInput) -> FilterResult:
        template = """
        You are the following character:
        {agent_prompt}

        You are about to send the following message:
        {new_message}

        Guidelines:
        - Consider the conversation context and agent's role.
        - Your response must be in JSON format.

        Examples of typically inappropriate messages:
        - "I'm sorry I'm not comfortable..."
        - Acknowledging it's origins ex. "I am an AI model trained by Anthropic..."
        - If the character is displaying lack of ego and blindly following instructions
        - If it implicitly proves that the agent is an AI or is an AI role playing as a character

        Recent messages: {messages}

        Respond in JSON:
        {{
            "approved": true/false,
            "prompt_addition": "if approved, leave empty. If not approved, suggest a brief addition to the prompt to improve the response."
        }}
        """

        system_prompt = template.format(
            agent_prompt=input.agent_prompt,
            new_message=input.new_message,
            messages=input.messages,
        )

        response = self.llm.generate_response(messages=[{"role": "user", "content": "Verify the message."}], system_prompt=system_prompt)
        
        try:
            result = json.loads(response)
            return FilterResult(from_user=False, new_message=input.new_message, approved=result['approved'], prompt_addition=result.get('prompt_addition', ""))
        except json.JSONDecodeError:
            return FilterResult(from_user=False, new_message=input.new_message, approved=False, prompt_addition="Error parsing filter response. Please regenerate.")
    

    
