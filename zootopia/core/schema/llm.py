from enum import Enum
from pydantic import BaseModel

class LLMNames(Enum):
    """Enumeration of available LLM models."""

    GPT_4O = "gpt-4o"
    GPT_35_TURBO = "gpt-3.5-turbo"

    CLAUDE_OPUS = "claude-3-opus-20240229"
    CLAUDE_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_HAIKU = "claude-3-haiku-20240307"

    GEMINI_PRO = "gemini-1.5-pro"
    GEMINI_FLASH = "gemini-1.5-flash"

    LLAMA3_8B = "llama3-8b-8192"
    LLAMA3_70B = "llama3-70b-8192"
    MIXTRAL = "mixtral-8x7b-32768"
    GEMMA = "gemma-7b-it"

class LLMConfig(BaseModel):
    """Configuration for an LLM instance."""
    name: LLMNames