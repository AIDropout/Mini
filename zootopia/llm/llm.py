from typing import List, Dict, Optional
import litellm

class LLM:
    """Class for Large Language Models (LLMs) usage powered by LiteLLM"""

    def __init__(self, llm_name: str):
        self.llm_name: str = llm_name
        litellm.modify_params = True

    def generate_response(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None, **kwargs) -> str:
        """
        Generate a response using the specified model.
        
        :param messages: List of message dictionaries with 'role' and 'content' keys
        :param system_prompt: Optional system prompt to guide the model's behavior
        :param kwargs: Additional arguments to pass to the litellm completion function
        :return: The generated response as a string
        """
        try:
            prepared_messages = messages
            if system_prompt:
                prepared_messages = [{"role": "system", "content": system_prompt}] + prepared_messages
            
            response = litellm.completion(model=self.llm_name, messages=prepared_messages, **kwargs)
            print("🔴🔴🔴")
            print(response)
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating response: {e}")
            return ""