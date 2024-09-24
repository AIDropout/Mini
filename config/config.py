import yaml
from pydantic import Field
from pydantic_settings import BaseSettings


class StripeConfig(BaseSettings):
    secret_key: str
    webhook_secret: str
    basic_weekly_price_id: str
    pro_weekly_price_id: str


class PromptRulesConfig(BaseSettings):
    initial_message_count: int
    initial_message_prompt: str

    last_conversation_days_threshold: int
    last_conversation_prompt: str

    pre_subscription_prompt: str
    post_subscription_prompt: str

    style_guidelines: dict


class PromptPersonalityConfig(BaseSettings):
    shy_level: int = Field(0, ge=0, le=100)
    confidence_level: int = Field(0, ge=0, le=100)
    assertiveness_level: int = Field(0, ge=0, le=100)
    friendliness_level: int = Field(0, ge=0, le=100)
    flirtiness_level: int = Field(0, ge=0, le=100)
    humor_level: int = Field(0, ge=0, le=100)


class PromptAboutConfig(BaseSettings):
    timezone: str
    interests: list[str]
    past_events: list[str]


class PromptMetadataConfig(BaseSettings):
    # requires logic refactor of other files
    # retrieved_message_count: int
    # retrieved_memory_count: int
    display_timestamp: bool


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
    website_webhook_url: str
    error_webhook_url: str
    message_webhook_url: str


class InstagramConfig(BaseSettings):
    api_version: str
    verify_token: str


class NgrokConfig:
    url: str | None = None

    def set_url(self, url: str):
        self.url = url

    def get_url(self) -> str:
        if self.url is None:
            raise ValueError("Ngrok URL not set")
        return self.url


class RenderConfig(BaseSettings):
    url: str


class Config(BaseSettings):
    ENVIRONMENT: str
    NGROK_CONFIG: NgrokConfig = NgrokConfig()
    RENDER_CONFIG: RenderConfig
    SCHEDULER_DB_URL: str
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
    SUPABASE_PROMPTS_BUCKET_NAME: str
    SUPABASE_AGENT_PROMPT_PATH: str
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
    VISION_MANAGER_LLM: str
    STRIPE_CONFIG: StripeConfig
    PHONE_OTP_CHANNEL_ID: str
    FRONTEND_URL: str
    TIME_API: TimeApiConfig = TimeApiConfig()
    MEMORY_GENERAL_LLM: str
    MEMORY_VECTOR_STORE_PROVIDER: str
    MEMORY_QDRANT_CONFIG: MemoryQdrantConfig
    MEMORY_LLM_PROVIDER: str
    MEMORY_LITELLM_CONFIG: MemoryLiteLLMConfig
    MEMORY_EMBEDDINGS_PROVIDER: str
    MEMORY_EMBEDDINGS_CONFIG: MemoryOpenAIConfig
    ENABLE_RESPONSE_DELAY: bool
    ENABLE_CELERY_BEAT: bool
    AWS_S3_CONFIG: AWSS3Config
    SECRET_PHRASES: SecretPhrases
    DISCORD_CONFIG: DiscordConfig
    INSTAGRAM_CONFIG: InstagramConfig

    @classmethod
    def from_yaml(cls, file_path: str):
        with open(file_path, "r") as file:
            yaml_data = yaml.safe_load(file)
        return cls(**yaml_data)

    def is_local(self) -> bool:
        """Returns True if the environment is local, otherwise False."""
        return self.ENVIRONMENT == "local"

    def is_production(self) -> bool:
        """Returns True if the environment is production, otherwise False."""
        return self.ENVIRONMENT == "prod"


# Create config instance from YAML
config = Config.from_yaml("config.yaml")
