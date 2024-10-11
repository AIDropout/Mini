from typing import Callable, Dict, List, Optional, Type, Union, cast
from uuid import uuid4

import litellm
from litellm import CustomStreamWrapper, completion
from litellm.types.utils import ModelResponse
from litellm.utils import get_supported_openai_params, supports_vision
from pydantic import BaseModel

from config.config import config
from mini.core.logger import get_logger

from .models import Model
from .provider import Provider
from .utils import execute_with_retry

logger = get_logger(__name__)


class LLMService:
    """Manages interactions with multiple Large Language Models using litellm."""

    def __init__(
        self,
        model: Model,
        api_key: str | None = None,
        cost_tracking_callback: Optional[Callable] = None,
    ):
        self.provider = model.provider
        self.model_name = model.model_name
        self.api_key = api_key or self._get_default_api_key()
        self.s3_file_prefix = f"{config.ENVIRONMENT}/{uuid4()}.wav"
        self.audio_content_type = "audio/mpeg"
        self.supports_json = self._check_json_support()
        self.supports_vision = self._check_vision_support()
        self.cost_tracking_callback = cost_tracking_callback
        litellm.success_callback = [self._success_callback]
        litellm.enable_json_schema_validation = True

    def _success_callback(
        self,
        kwargs,
        completion_response,
        start_time,
        end_time,
    ):
        response_cost: float = kwargs.get("response_cost", 0)
        logger.info("🤑 streaming response_cost: %s", response_cost)

        if self.cost_tracking_callback is not None:
            logger.info("Updating cost tracking callback")
            self.cost_tracking_callback(response_cost)

    def _get_default_api_key(self) -> str | None:
        """Get the default API key from config based on the provider."""
        key_mapping = {
            Provider.ANTHROPIC: config.ANTHROPIC_API_KEY,
            Provider.OPENAI: config.OPENAI_API_KEY,
            Provider.GEMINI: config.GEMINI_API_KEY,
            Provider.GROQ: config.GROQ_API_KEY,
        }
        return key_mapping.get(self.provider)

    def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        json_mode: Optional[bool] = False,
        response_format: Optional[Union[BaseModel, Type[BaseModel]]] = None,
        **kwargs,
    ) -> Union[str, Dict]:
        """Generate a response using the specified model."""
        prepared_messages = self._prepare_messages(messages)

        if self.provider == Provider.ANTHROPIC:
            # Anthropic requires system prompt to be sent separately
            kwargs["system"] = system_prompt
            # Ensure first message is user content (Anthropic-specific requirement)
            if not prepared_messages or prepared_messages[0]["role"] != "user":
                prepared_messages.insert(0, {"role": "user", "content": "-"})
        else:
            prepared_messages.insert(0, {"role": "system", "content": system_prompt})

        if json_mode and self.supports_json:
            kwargs["response_format"] = {"type": "json_object"}
        elif json_mode and not self.supports_json:
            logger.warning("Model %s does not support JSON mode", self.model_name)

        if response_format and self.supports_json:
            kwargs["response_format"] = response_format
        elif response_format and not self.supports_json:
            logger.warning(
                "Model %s does not support JSON response formatting", self.model_name
            )

        completion_kwargs = {
            "api_key": self.api_key,
            "model": self.model_name,
            "messages": prepared_messages,
            **kwargs,
        }
        content: ModelResponse | CustomStreamWrapper = execute_with_retry(
            completion, **completion_kwargs
        )
        generated_message: str | None = content.choices[0].message.content
        return generated_message

    def describe_images(self, system_prompt: str, image_urls: List[str]) -> str:
        """Generate descriptions for images."""
        if not self.supports_vision:
            raise ValueError(f"Model {self.model_name} does not support vision tasks.")
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": url}}
                    for url in image_urls
                ],
            },
        ]
        return cast(str, self.generate_response(messages, system_prompt))

    def _prepare_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Prepare messages by combining consecutive user messages."""
        prepared = []
        for msg in messages:
            if prepared and prepared[-1]["role"] == msg["role"] == "user":
                prepared[-1]["content"] += f" | {msg['content']}"
            else:
                prepared.append(msg)
        if prepared and prepared[-1]["role"] == "assistant":
            prepared.append({"role": "user", "content": "[ignore]"})
        return prepared

    def _check_json_support(self) -> bool:
        """Check if the model supports JSON mode."""
        return "response_format" in get_supported_openai_params(model=self.model_name)  # type: ignore

    def _check_vision_support(self) -> bool:
        """Check if the model supports vision tasks."""
        return supports_vision(model=self.model_name)
