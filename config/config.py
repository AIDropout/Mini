import yaml
from pydantic_settings import BaseSettings

from mini.core.schema.llm import LLMProviders


def get_api_key(provider: LLMProviders) -> str:
    """Fetches the API key from the config based on the provider."""
    return getattr(config, provider.value)


class UserRateLimits(BaseSettings):
    # TODO: implement
    # IDEA: when max images are sent, sam's phone 'stops reciving images'
    # IDEA: wehn max texts are sent, we can tune down sam's responses, or change his
    # schedule so that he's now 'busy' -- doesn't have to be complex
    # can also just stop messaging for the day, and apologize with proactive
    max_texts_per_day: int
    max_images_per_day: int


class MemoryQdrantConfig(BaseSettings):
    url: str
    api_key: str
    collection_name: str
    embedding_model_dims: int


class MemoryLiteLLMConfig(BaseSettings):
    model: str
    temperature: float
    max_tokens: int
    api_key: str


class TimeApiConfig(BaseSettings):
    url_from_timezone: str = "https://timeapi.io/api/time/current/zone?timeZone="
    url_from_ip: str = "https://timeapi.io/api/time/current/ip?ipAddress="
    url_available_timezones: str = "https://timeapi.io/api/timezone/availabletimezones"
    default_timezone: str = "America/Chicago"


class AWSS3Config(BaseSettings):
    access_key: str
    secret_access_key: str
    bucket: str


class MemoryOpenAIConfig(BaseSettings):
    model: str
    embedding_dims: int
    api_key: str


class SecretPhrases(BaseSettings):
    reset_user: str

class DiscordConfig(BaseSettings):
    webhook_url: str


class Config(BaseSettings):
    ENVIRONMENT: str
    BACKEND_API_KEY: str
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str
    GROQ_API_KEY: str
    TELEGRAM_BOT_TOKEN: str
    BIRD_API_URL: str = "https://api.bird.com"
    BIRD_API_KEY: str
    BIRD_ORGANIZATION_ID: str
    BIRD_WORKSPACE_ID: str
    BIRD_DEV_CHANNEL_ID: str
    BIRD_SIGNING_KEY: str
    SUPABASE_URL: str
    SUPABASE_KEY: str
    GOOGLE_API_KEY: str
    GEMINI_API_KEY: str
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    REDIS_URL: str
    FLOWER_UNAUTHENTICATED_API: bool
    FILTER_LLM: str
    SKIP_LLM: str
    ACTION_MANAGER_LLM_PROVIDER: LLMProviders
    ACTION_MANAGER_LLM: str
    INTENT_MANAGER_LLM: str
    MEMORY_MANAGER_LLM: str
    VISION_MANAGER_LLM: str
    VISION_MANAGER_LLM_PROVIDER: LLMProviders
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    STRIPE_PRODUCT_PRICE_ID: str
    PHONE_OTP_CHANNEL_ID: str
    FRONTEND_URL: str
    TIME_API: TimeApiConfig = TimeApiConfig()
    MEMORY_GENERAL_LLM: str
    MEMORY_GENERAL_LLM_PROVIDER: LLMProviders
    MEMORY_VECTOR_STORE_PROVIDER: str
    MEMORY_QDRANT_CONFIG: MemoryQdrantConfig
    MEMORY_LLM_PROVIDER: str
    MEMORY_LITELLM_CONFIG: MemoryLiteLLMConfig
    MEMORY_EMBEDDINGS_PROVIDER: str
    MEMORY_EMBEDDINGS_CONFIG: MemoryOpenAIConfig
    ENABLE_RESPONSE_DELAY: bool
    AWS_S3_CONFIG: AWSS3Config
    SECRET_PHRASES: SecretPhrases
    DISCORD_CONFIG: DiscordConfig

    @classmethod
    def from_yaml(cls, file_path: str):
        with open(file_path, "r") as file:
            yaml_data = yaml.safe_load(file)
        return cls(**yaml_data)


# Create config instance from YAML
config = Config.from_yaml("config.yaml")
