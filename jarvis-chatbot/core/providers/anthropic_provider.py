"""Provedor Anthropic - integração com a API Claude."""

from typing import Generator
from anthropic import Anthropic
from .base import AIProvider


class AnthropicProvider(AIProvider):
    @property
    def name(self) -> str:
        return "Anthropic"

    @property
    def default_model(self) -> str:
        return "claude-sonnet-4-20250514"

    @property
    def available_models(self) -> list[str]:
        return ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"]

    def _model_context_map(self) -> dict[str, int]:
        return {
            "claude-sonnet-4-20250514": 200000,
            "claude-3-5-sonnet-20241022": 200000,
            "claude-3-5-haiku-20241022": 200000,
            "claude-3-opus-20240229": 200000,
            "claude-3-haiku-20240307": 200000,
        }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.api_key:
            self.client = Anthropic(api_key=self.api_key)

    def send_message(self, messages: list[dict], stream: bool = False) -> Generator[str, None, None] | str:
        self._ensure_client(Anthropic, api_key=self.api_key)

        system = ""
        filtered = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                filtered.append(msg)

        kwargs = dict(model=self.model, max_tokens=self.max_tokens, temperature=self.temperature)
        if system:
            kwargs["system"] = system

        if stream:
            stream_response = self.client.messages.stream(messages=filtered, **kwargs)
            def gen():
                with stream_response:
                    for text in stream_response.text_stream:
                        yield text
            return gen()
        response = self.client.messages.create(messages=filtered, **kwargs)
        return response.content[0].text if response.content else ""