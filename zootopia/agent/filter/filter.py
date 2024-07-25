from typing import Optional
from zootopia.llm.llm import LLM  
from config.config import Config, IntentManagerConfig, ActionManagerConfig, MemoryManagerConfig, FilterConfig


class MessageFilter:
    def __init__(self, message: str, llm: Optional[LLM] = None):
        self.message = message
        self.is_appropriate: Optional[bool] = None
        self.llm = llm or LLM("your-default-model-name")
        self._reason: Optional[str] = None
    
    @classmethod
    def from_config(cls, filter_config: ActionManagerConfig) -> "MessageFilter":
        model_name = filter_config.LLM_NAME
        return cls(
            model_name
        )
    

    def check_appropriateness(self) -> bool:
        if self.is_appropriate is None:
            prompt = f"Determine if the following message is appropriate for a chatbot. Respond with 'YES' or 'NO' followed by a brief explanation:\n\n{self.message}"
            response = self.llm.generate_response([{"role": "user", "content": prompt}])
            
            self.is_appropriate = response.strip().upper().startswith("YES")
            self._reason = response.strip()[3:] 
        
        return self.is_appropriate

    @property
    def reason(self) -> Optional[str]:
        if self._reason is None and self.is_appropriate is not None:
            self.check_appropriateness() 
        return self._reason

    def __repr__(self) -> str:
        return f"MessageFilter(message='{self.message}', is_appropriate={self.is_appropriate})"