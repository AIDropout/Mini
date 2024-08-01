import re
from typing import Dict, Any, Optional
from pydantic import BaseModel, create_model

def is_ngrok_url(url: str) -> bool:
    ngrok_pattern = r'^https?://[a-zA-Z0-9-]+\.ngrok-free\.app'
    return bool(re.match(ngrok_pattern, url))

class DynamicResponseModel(BaseModel):
    @classmethod
    def create_model_from_json(cls, json_schema: Dict[str, Any]):
        fields = {}
        for intent, schema in json_schema.items():
            if schema['type'] == 'object':
                fields[intent] = (Optional[Dict[str, Any]], None)
        return type('DynamicModel', (BaseModel,), fields)