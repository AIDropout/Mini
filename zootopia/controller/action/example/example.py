"""
Example file using intent with a yaml config

Steps:
- add .env file based on .env.example
- run `python -m zootopia.intent.example.example`
"""

from dotenv import load_dotenv

from zootopia.controller.intent.intent import IntentConfig, IntentManager
from zootopia.core.utils.utils import load_yaml_config

load_dotenv()

intent_config = load_yaml_config(
    config_path="zootopia/intent/example/example.yaml", config_type=IntentConfig
)

