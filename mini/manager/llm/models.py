from enum import Enum

from .provider import Provider


class Model(Enum):
    GPT_4 = ("gpt-4", Provider.OPENAI)
    GPT_4O_MINI = ("gpt-4o-mini", Provider.OPENAI)
    GPT_3_5_TURBO = ("gpt-3.5-turbo", Provider.OPENAI)
    GEMINI_1_5_PRO = ("gemini/gemini-1.5-flash", Provider.GEMINI)
    GEMINI_1_5_FLASH = ("gemini/gemini-1.5-flash", Provider.GEMINI)
    CLAUDE_3_5_SONNET = ("claude-3-5-sonnet-20240620", Provider.ANTHROPIC)
    CLAUDE_3_HAIKU = ("claude-3-haiku-20240307", Provider.ANTHROPIC)
    GROQ_LLAMA_70B = ("groq/llama-3.1-70b-versatile", Provider.GROQ)

    def __init__(self, model_name: str, provider: Provider):
        self.model_name = model_name
        self.provider = provider

    @classmethod
    def from_model_name(cls, model_name: str):
        """Convert a model name string to a Model enum instance."""
        for model in cls:
            if model.model_name == model_name:
                return model
        raise ValueError(f"No Model found for model_name: {model_name}")
