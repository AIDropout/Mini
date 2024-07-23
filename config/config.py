import os
import re
from typing import Any, Dict, List, Union
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

class MessagingConfig(BaseModel):
    TELEGRAM: TelegramConfig
    BIRD: BirdConfig

class ActionManagerConfig(BaseModel):
    LLM_NAME: str

class IntentManagerConfig(BaseModel):
    LLM_NAME: str

class MemoryManagerConfig(BaseModel):
    LLM_NAME: str

ManagerConfig = Union[ActionManagerConfig, IntentManagerConfig, MemoryManagerConfig]

class TaskManagerConfig(BaseModel):
    REDIS_URL: str

class BehaviorsConfig(BaseModel):
    ACTION_MANAGER: ActionManagerConfig
    INTENT_MANAGER: IntentManagerConfig
    MEMORY_MANAGER: MemoryManagerConfig
    TASK_MANAGER: TaskManagerConfig

class WebAccessConfig(BaseModel):
    GOOGLE: Dict[str, Any]

class Config(BaseModel):
    DATABASE_CONFIG: DatabaseConfig
    MESSAGING_CONFIG: MessagingConfig
    BEHAVIORS_CONFIG: BehaviorsConfig
    WEB_ACCESS_CONFIG: WebAccessConfig

def replace_env_vars(value: Any) -> Any:
    if isinstance(value, str):
        pattern = r'\$\{([^}^{]+)\}'
        matches = re.finditer(pattern, value)
        for match in matches:
            env_var = match.group(1)
            env_value = os.getenv(env_var)
            if env_value is not None:
                value = value.replace(match.group(0), env_value)
            else:
                raise ValueError(f"Environment variable {env_var} is not set")
    elif isinstance(value, dict):
        return {k: replace_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [replace_env_vars(v) for v in value]
    return value

def load_config(config_path: str, set_env: bool = False) -> Config:
    with open(config_path, "r", encoding="utf-8") as config_file:
        config_data = yaml.safe_load(config_file)
    
    # Replace ${___} with environment variables
    config_data = replace_env_vars(config_data)

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