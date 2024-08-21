import yaml
from pydantic_settings import BaseSettings


# Load YAML configuration
def load_yaml_config(file_path: str):
    with open(file_path, "r") as file:
        return yaml.safe_load(file)


yaml_config = load_yaml_config("config.yaml")


class MemoryQdrantConfig(BaseSettings):
    url: str
    api_key: str
    collection_name: str
    embedding_model_dims: int


class MemoryLiteLLMConfig(BaseSettings):
    model: str
    temperature: float
    max_tokens: int


class Config(BaseSettings):
    ENVIRONMENT: str
    ZOOTOPIA_API_KEY: str
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
    ACTION_MANAGER_LLM: str
    INTENT_MANAGER_LLM: str
    MEMORY_MANAGER_LLM: str
    STRIPE_SECRET_KEY_TEST: str
    STRIPE_WEBHOOK_SECRET: str
    STRIPE_PRODUCT_PRICE_ID: str
    PHONE_OTP_CHANNEL_ID: str
    FRONTEND_URL: str
    MEMORY_VECTOR_STORE_PROVIDER: str
    MEMORY_QDRANT_CONFIG: MemoryQdrantConfig
    MEMORY_LLM_PROVIDER: str
    MEMORY_LITELLM_CONFIG: MemoryLiteLLMConfig

    @classmethod
    def from_yaml(cls, yaml_data: dict):
        return cls(**yaml_data)


# Create config instance from YAML
config = Config.from_yaml(yaml_config)
