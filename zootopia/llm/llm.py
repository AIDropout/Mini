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

    def generate_stream(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None, **kwargs):
        """
        Generate a streaming response using the specified model.
        
        :param messages: List of message dictionaries with 'role' and 'content' keys
        :param system_prompt: Optional system prompt to guide the model's behavior
        :param kwargs: Additional arguments to pass to the litellm completion function
        :return: A generator yielding response chunks
        """
        try:
            prepared_messages = self._prepare_messages(messages, system_prompt)
            response = litellm.completion(model=self.llm_name, messages=prepared_messages, stream=True, **kwargs)
            for chunk in response:
                yield chunk.choices[0].delta.content or ""
        except Exception as e:
            print(f"Error generating streaming response: {e}")
            yield ""


# Example usage:
if __name__ == "__main__":
    # Initialize LLM with a specific model
    llm = LLM("gpt-3.5-turbo")

    # Define a system prompt
    system_prompt = "You are a helpful assistant that speaks like a pirate."

    # Generate a response with system prompt
    messages = [{"role": "user", "content": "Tell me about the weather today."}]
    response = llm.generate_response(messages, system_prompt=system_prompt)
    print("Generated response:", response)

    # Generate a streaming response with system prompt
    print("\nStreaming response:")
    for chunk in llm.generate_stream(messages, system_prompt=system_prompt):
        print(chunk, end="", flush=True)
    print()

    # Generate a response without system prompt
    messages = [{"role": "user", "content": "What's the capital of France?"}]
    response = llm.generate_response(messages)
    print("\nGenerated response without system prompt:", response)