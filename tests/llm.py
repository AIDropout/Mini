from pydantic_settings import BaseSettings

from mini.llm import LLMService, Model

# should automatically detect api key from config
llm_service = LLMService(model=Model.CLAUDE_3_5_SONNET)


# making a response format
class ResponseFormat(BaseSettings):
    text: str
    reasoning: str


response_format = ResponseFormat(
    text="insert the best response here",
    reasoning="adjectives describing reasoning for the best response",
)


res = llm_service.generate_response(
    messages=[],
    system_prompt="insert the system prompt here",
    response_format=response_format.model_dump_json(),
)


print(res)
