from typing import Callable, Dict, List, Optional, Union
from uuid import uuid4

import litellm
import weave
from litellm import completion, speech
from litellm.types.utils import ModelResponse
from litellm.utils import get_supported_openai_params, supports_vision

from config.config import config
from mini.core.logger import get_logger
from mini.storage.s3 import S3FileStore

from .models import Model
from .provider import Provider
from .utils import execute_with_retry, parse_content

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
        weave.init("aibf_dev")

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

    @weave.op()
    def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        json_mode: Optional[bool] = False,
        **kwargs,
    ) -> Union[str, Dict]:
        """Generate a response using the specified model."""
        prepared_messages = [{"role": "system", "content": system_prompt}]
        prepared_messages.extend(self._prepare_messages(messages))

        if json_mode and self.supports_json:
            kwargs["response_format"] = {"type": "json_object"}

        completion_kwargs = {
            "model": self.model_name,
            "messages": prepared_messages,
            **kwargs,
        }
        content: ModelResponse = execute_with_retry(completion, **completion_kwargs)
        generated_message: str = content.choices[0].message.content

        return parse_content(
            generated_message,
            completion_kwargs.get("response_format", None),
        )

    def generate_speech(self, text: str, voice: str) -> tuple:
        """Generate speech and upload to S3."""
        audio_content = speech(model=self.model_name, voice=voice, input=text).content
        return self._upload_audio(audio_content)

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
        return self.generate_response(messages, system_prompt)

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

    def _upload_audio(self, audio_content: bytes) -> tuple:
        """Upload audio content to S3 and return URL."""
        fs = S3FileStore()
        fs.write(self.s3_file_prefix, audio_content, self.audio_content_type)
        return (
            fs.generate_presigned_url(self.s3_file_prefix, self.audio_content_type),
            self.audio_content_type,
        )

    def _check_json_support(self) -> bool:
        """Check if the model supports JSON mode."""
        return "response_format" in get_supported_openai_params(model=self.model_name)  # type: ignore

    def _check_vision_support(self) -> bool:
        """Check if the model supports vision tasks."""
        return supports_vision(model=self.model_name)
