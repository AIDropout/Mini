import os
from dotenv import load_dotenv
from enum import Enum

load_dotenv(override=True)

class LLMNames(Enum):
    """Enumeration of available LLM models."""

    GPT_4O = "gpt-4o"
    GPT_35_TURBO = "gpt-3.5-turbo"

    CLAUDE_OPUS = "claude-3-opus-20240229"
    CLAUDE_SONNET = "claude-3-5-sonnet-20240620"
    CLAUDE_HAIKU = "claude-3-haiku-20240307"

    GEMINI_PRO = "gemini-1.5-pro"
    GEMINI_FLASH = "gemini-1.5-flash"

    LLAMA3_8B = "llama3-8b-8192"
    LLAMA3_70B = "llama3-70b-8192"
    MIXTRAL = "mixtral-8x7b-32768"
    GEMMA = "gemma-7b-it"

class Config:
    """URLS"""
    SIGNUP_LIVE_URL = "https://www.aibf.rsvp"
    SIGNUP_LOCAL_URL = "http://localhost:3000"
    SUBSCRIBE_URL = "https://www.aibf.rsvp/subscribe"

    """API Secrets"""
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")

    BIRD_ORGANIZATION_ID: str = os.getenv("BIRD_ORGANIZATION_ID")
    BIRD_WORKSPACE_ID: str = os.getenv("BIRD_WORKSPACE_ID")
    BIRD_API_KEY: str = os.getenv("BIRD_API_KEY")
    BIRD_SIGNING_KEY: str = os.getenv("BIRD_SIGNING_KEY")
    BIRD_CHANNEL_ID: str = os.getenv("BIRD_CHANNEL_ID")
    BIRD_ACCESS_KEY: str = os.getenv("BIRD_ACCESS_KEY")

    SUPABASE_URL: str = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY")

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://127.0.0.1")
    
    """ Configurable AI providers and models for prompts """
    ACTION_MANAGER_MODEL = LLMNames.CLAUDE_SONNET
    INTENT_MANAGER_MODEL = LLMNames.CLAUDE_SONNET
    MEMORY_MANAGER_MODEL = LLMNames.CLAUDE_SONNET

    PROMPT = """
    You are Sam Asher, a fun cool lively flirtateous dynamic loveable long-distance boyfriend texting your partner.
    - You've never met them before.
    - only know english, bad spanish
    - use lowercase
    - use slang
    - read the room: if their texts are short, match. if they're excited & typing all caps, match.

    IMPORTANT:
    - NO exclamation marks, periods, questions
    - NO emojis
    - NO repetition
    - DON'T BE cheesy/corny/cringe
    - NO unnecessary profanity
    - NO calls/facetime
        """



config = Config()
