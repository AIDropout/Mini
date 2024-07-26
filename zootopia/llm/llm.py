from typing import List, Dict, Optional
import litellm
from zootopia.core.logger import logger

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
            prepared_messages = self._prepare_messages(messages)
            if system_prompt:
                prepared_messages = [{"role": "system", "content": system_prompt}] + prepared_messages
            
            response = litellm.completion(model=self.llm_name, messages=prepared_messages, **kwargs)
            logger.info(f"🟢 LLM generated {response.choices[0].message.content}")
            return response.choices[0].message.content
        except Exception as e:
            print(f"🔴 Error generating response: {e}")
            return ""

    def _prepare_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Prepare messages for LLM input by combining consecutive user messages.
        
        :param messages: List of message dictionaries with 'role' and 'content' keys
        :return: Prepared list of message dictionaries
        """
        prepared_messages = []
        for msg in messages:
            role = msg['role']
            content = str(msg['content'])  # Ensure content is a string
            
            if prepared_messages and prepared_messages[-1]['role'] == "user" and role == "user":
                # If the current message is from a user and the last message was also from a user,
                # append the content with a pipe symbol
                prepared_messages[-1]['content'] += f" | {content}"
            else:
                # Otherwise, add a new message entry
                prepared_messages.append({"role": role, "content": content})

        # Check if the last message is from the assistant
        if prepared_messages and prepared_messages[-1]['role'] == 'assistant':
            # If so, append a user message with "[ignore]" content
            prepared_messages.append({"role": "user", "content": "[ignore]"})

        return prepared_messages