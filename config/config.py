import os
from typing import Any, Dict, List
from pydantic import BaseModel
import yaml

# Manual type definitions
class SupabaseConfig(BaseModel):
    URL: str
    KEY: str

class DatabaseConfig(BaseModel):
    SUPABASE: SupabaseConfig

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

class LLMConfig(BaseModel):
    GEMINI: Dict[str, str]
    GROQ: Dict[str, str]
    OPENAI: Dict[str, str]
    ANTHROPIC: Dict[str, str]

class ActionManagerConfig(BaseModel):
    MODEL: str

class IntentManagerConfig(BaseModel):
    MODEL: str

class MemoryManagerConfig(BaseModel):
    MODEL: str

class TaskManagerConfig(BaseModel):
    REDIS_URL: str

class BehaviorsConfig(BaseModel):
    PROMPT: str
    ACTION_MANAGER: ActionManagerConfig
    INTENT_MANAGER: IntentManagerConfig
    MEMORY_MANAGER: MemoryManagerConfig
    TASK_MANAGER: TaskManagerConfig

class WebAccessConfig(BaseModel):
    GOOGLE: Dict[str, Any]  # You might want to define a more specific type here

class Config(BaseModel):
    DATABASE_CONFIG: DatabaseConfig
    MESSAGING_CONFIG: MessagingConfig
    LLM_CONFIG: LLMConfig
    BEHAVIORS_CONFIG: BehaviorsConfig
    WEB_ACCESS_CONFIG: WebAccessConfig

# Config loading function
def load_config(config_path: str, set_env: bool = False) -> Config:
    with open(config_path, "r", encoding="utf-8") as config_file:
        config_data = yaml.safe_load(config_file)

    if set_env:
        set_environment_variables(config_data)

    return Config(**config_data)

def set_environment_variables(config_data: Dict[str, Any], prefix: str = ""):
    for key, value in config_data.items():
        env_key = f"{prefix}_{key}" if prefix else key
        if isinstance(value, dict):
            set_environment_variables(value, env_key)
        else:
            os.environ[env_key] = str(value)

# Load the configuration
testing = True
prefix = "config/" if testing else "/etc/secrets/"
config = load_config(f"{prefix}local.yaml", set_env=True)

# Export the config instance and the Config type
__all__ = ['config', 'Config']