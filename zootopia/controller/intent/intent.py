from typing import List, Dict, Union
from zootopia.core.schema import MessageTableModel, Action, ActionType
from zootopia.llm.llm import LLM 
from zootopia.core.utils.utils import clean_and_parse_llm_json_output, render_jinja_template
import json
from config.config import IntentManagerConfig

class IntentManager:
    def __init__(self, model_name: str):
        self.llm = LLM(model_name)

    @classmethod
    def from_config(cls, manager_config: IntentManagerConfig) -> "IntentManager":
        model_name = manager_config.LLM_NAME
        return cls(
            model_name,
        )
    
    def produce_actions(self, recent_messages: List[Dict[str, str]], possible_actions: List[str]) -> List[Action]:
        history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_messages])

        actions_str = ", ".join(possible_actions)

        response_structure = {
            "action": "action_name",
            "args": {
                "key1": "value1",
                "key2": "value2"
            }
        }

        prompt = render_jinja_template(
            "autonomous.jinja",
            "zootopia/controller/intent/templates",
            message_history=history_str,
            possible_actions=actions_str,
            response_structure=json.dumps(response_structure, indent=2)
        )

        content = self.llm.generate_response([{"role": "user", "content": prompt}])
        cleaned = clean_and_parse_llm_json_output(content)

        if isinstance(cleaned, dict) and 'action' in cleaned and 'args' in cleaned:
            action_type = cleaned['action']
            if action_type in possible_actions:
                return [Action(type=action_type, args=cleaned['args'])]
            else:
                print(f"Invalid action type: {action_type}")
        else:
            print(f"Unexpected response structure: {cleaned}")

        return []  # Return an empty list if no valid action was found