from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Config(BaseSettings):
    ZOOTOPIA_API_KEY: str = Field(..., env="ZOOTOPIA_API_KEY")
    SUPABASE_URL: str = Field(..., env="SUPABASE_URL")
    SUPABASE_KEY: str = Field(..., env="SUPABASE_KEY")
    TELEGRAM_BOT_TOKEN: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    BIRD_API_URL: str = Field("https://api.bird.com")
    BIRD_ORGANIZATION_ID: str = Field(..., env="BIRD_ORGANIZATION_ID")
    BIRD_WORKSPACE_ID: str = Field(..., env="BIRD_WORKSPACE_ID")
    BIRD_API_KEY: str = Field(..., env="BIRD_API_KEY")
    BIRD_SIGNING_KEY: str = Field(..., env="BIRD_SIGNING_KEY")
    REDIS_URL: str = Field(..., env="REDIS_URL")
    FILTER_LLM: str = Field("groq/llama-3.1-70b-versatile", env="FILTER_LLM")
    SKIP_LLM: str = Field("groq/llama-3.1-70b-versatile", env="SKIP_LLM")
    ACTION_MANAGER_LLM: str = Field(
        "claude-3-5-sonnet-20240620", env="ACTION_MANAGER_LLM"
    )
    INTENT_MANAGER_LLM: str = Field(
        "claude-3-5-sonnet-20240620", env="INTENT_MANAGER_LLM"
    )
    MEMORY_MANAGER_LLM: str = Field(
        "claude-3-5-sonnet-20240620", env="MEMORY_MANAGER_LLM"
    )
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    STRIPE_SECRET_KEY_TEST: str = Field(..., env="STRIPE_SECRET_KEY_TEST")
    STRIPE_WEBHOOK_SECRET: str = Field(..., env="STRIPE_WEBHOOK_SECRET")

    STRIPE_PRODUCT_PRICE_ID: str = Field(..., env="STRIPE_PRODUCT_LOOKUP_KEY")
    PHONE_OTP_CHANNEL_ID: str = Field(..., env="PHONE_OTP_CHANNEL_ID")
    FRONTEND_URL: str = Field(..., env="FRONTEND_URL")


config = Config()
