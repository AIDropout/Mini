from enum import Enum


class LLMProviders(Enum):
    GEMINI = "GEMINI_API_KEY"
    OPENAI = "OPENAI_API_KEY"
    ANTHROPIC = "ANTHROPIC_API_KEY"
    GROQ = "GROQ_API_KEY"
