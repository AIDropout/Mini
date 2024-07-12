"""
Example file using intent with a yaml config

Steps:
- add .env file based on .env.example
- run `python -m zootopia.intent.example.example`
"""

from dotenv import load_dotenv

from archive._intent import IntentConfig, IntentManager
from zootopia.core.utils.utils import load_yaml_config

load_dotenv()

intent_config = load_yaml_config(
    config_path="zootopia/intent/example/example.yaml", config_type=IntentConfig
)

intent_detector = IntentManager.from_config(config=intent_config)

test_inputs = [
    "Hi my name is X",
    "See ya bro!",
    "Can you help me with something?",
    "What's the capital of France?",
    "I don't understand, can you explain that again?",
    "What do you think about artificial intelligence?",
    "Please set a timer for 5 minutes.",
    "This service has been really helpful, thank you!",
    "How's the weather today?",
    "The quality of this product is terrible.",
    "Thank you so much for your help!",
    "I'm sorry for the confusion earlier.",
]

for input_text in test_inputs:
    print(f"Input: {input_text}")
    print(intent_detector.detect_intent(input_text))
    print()
