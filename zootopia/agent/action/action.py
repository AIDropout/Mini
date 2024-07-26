from typing import List, Dict, Optional
from zootopia.core.schema import Action, ActionType, ActionResult
from zootopia.core.logger import logger
from zootopia.llm import LLM 
from config.config import ActionManagerConfig
from zootopia.platform.platform import MessageProviderBase

class ActionManager:
    def __init__(self, model_name: str, messaging_service: MessageProviderBase) -> None:
        self.llm = LLM(model_name)
        self.messaging_service = messaging_service
    
    @classmethod
    def from_config(cls, manager_config: ActionManagerConfig, messaging_service: MessageProviderBase) -> "ActionManager":
        model_name = manager_config.LLM_NAME
        return cls(
            model_name, messaging_service
        )
    
    def generate_message(self, messages: List[Dict[str, str]], system_prompt: Optional[str], ) -> Optional[str]:
        msg = self.llm.generate_response(messages, system_prompt)
        return msg
        
    async def send_message(self, msg: str) -> None:
        await self.messaging_service.send_message(msg)