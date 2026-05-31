"""Provedor OpenAI - integração com a API da OpenAI."""

from typing import Generator
from openai import OpenAI
from .base import AIProvider


class OpenAIProvider(AIProvider):
    @property
    def name(self) -> str:
        return "OpenAI"

    @property
    def default_model(self) -> str:
        return "gpt-4o"

    @property
    def available_models(self) -> list[str]:
        return ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo", "o1", "o3-mini"]

    def _model_context_map(self) -> dict[str, int]:
        return {
            "gpt-4o": 128000,
            "gpt-4o-mini": 128000,
            "gpt-4-turbo": 128000,
            "gpt-4": 8192,
            "gpt-3.5-turbo": 16384,
            "o1": 200000,
            "o3-mini": 200000,
        }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)

    def send_message(self, messages: list[dict], stream: bool = False) -> Generator[str, None, None] | str:
        self._ensure_client(OpenAI, api_key=self.api_key)
        formatted = self.format_messages(messages)
        kwargs = dict(model=self.model, messages=formatted, stream=stream)
        if self.model not in ("o1", "o3-mini"):
            kwargs["max_tokens"] = self.max_tokens
            kwargs["temperature"] = self.temperature

        response = self.client.chat.completions.create(**kwargs)
        if stream:
            def gen():
                for chunk in response:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        yield delta.content
            return gen()
        return response.choices[0].message.content or ""