import os
from enum import Enum
from typing import cast, Optional, List

import yaml
from pydantic import BaseModel, ValidationError

from archive.autodb_config.models import SupabaseConfig, _UserIDConfig
from zootopia.apis.gsuite.models import GAuthConfig
from zootopia.core.schema import LLMConfig

class CalendarConfig(BaseModel):
    CALENDAR_NAME: str
    CALENDAR_DESCRIPTION: str

class DriveConfig(BaseModel):
    FOLDER_NAME: str
    FILE_NAME_FORMAT: str

class GAuthConfig(BaseModel):
    GOOGLE_API_KEY: str
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_AUTH_SCOPE: List[str]
    CALENDAR: CalendarConfig
    DRIVE: DriveConfig

class WebAccessConfig(BaseModel):
    GOOGLE: GAuthConfig

class TelegramConfig(BaseModel):
    TELEGRAM_BOT_TOKEN: str

class BirdConfig(BaseModel):
    BIRD_API_URL: str
    BIRD_ORGANIZATION_ID: str
    BIRD_WORKSPACE_ID: str
    BIRD_API_KEY: str
    BIRD_SIGNING_KEY: str
    BIRD_CHANNEL_ID: str

class MessagingConfig(BaseModel):
    TELEGRAM: TelegramConfig
    BIRD: BirdConfig

class SupabaseConfig(BaseModel):
    URL: str
    KEY: str

class DatabaseConfig(BaseModel):
    SUPABASE: SupabaseConfig

class LLMConfig(BaseModel):
    GEMINI: dict[str, str]
    GROQ: dict[str, str]
    OPENAI: dict[str, str]
    ANTHROPIC: dict[str, str]

class IntentDetectionConfig(BaseModel):
    MODEL: str

class HumanLikeMemoryConfig(BaseModel):
    MODEL: str

class TaskManagerConfig(BaseModel):
    REDIS_URL: str

class BehaviorsConfig(BaseModel):
    PROMPT: str
    INTENT_DETECTION: IntentDetectionConfig
    HUMAN_LIKE_MEMORY: HumanLikeMemoryConfig
    INTERNET_ACCESS: Optional[dict]
    TASK_MANAGER: TaskManagerConfig

class ZootopiaConfig(BaseModel):
    MESSAGING_CONFIG: MessagingConfig
    DATABASE_CONFIG: DatabaseConfig
    LLM_CONFIG: LLMConfig
    BEHAVIORS_CONFIG: BehaviorsConfig
    WEB_ACCESS_CONFIG: WebAccessConfig


def set_environment_variables(config_data, prefix=""):
    """
    Set environment variables from the configuration data.
    """
    for key, value in config_data.items():
        env_key = f"{prefix}_{key}" if prefix else key
        if isinstance(value, dict):
            set_environment_variables(value, env_key)
        else:
            os.environ[env_key] = str(value)


def load_config(
    config_path: str, set_env: bool = False, config_type: type[ZootopiaConfig] = ZootopiaConfig
) -> BaseModel:
    """Loads configuration from a YAML file."""

    with open(config_path, "r", encoding="utf-8") as config_file:
        config_data = yaml.safe_load(config_file)

    if set_env:
        set_environment_variables(config_data)

    try:
        return config_type(**config_data)
    except ValidationError as e:
        raise ValueError(f"Error parsing configuration: {e}") from e


testing = True
prefix = "config/" if testing else "/etc/secrets/"
config = cast(ZootopiaConfig, load_config(f"{prefix}local.yaml", set_env=True))
autodb_config = cast(
    AutoDBConfig, load_config("config/autodb.yaml", config_type=AutoDBConfig)
)

UserIDType = Enum(
    "UserIDType", [(field, field) for field in _UserIDConfig.model_fields]
)
