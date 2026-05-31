from typing import Generator
from openai import OpenAI
from .base import AIProvider


class OpenRouterProvider(AIProvider):
    @property
    def name(self) -> str:
        return "OpenRouter"

    @property
    def default_model(self) -> str:
        return "openai/gpt-4o"

    @property
    def available_models(self) -> list[str]:
        return [
            "openai/gpt-4o", "openai/gpt-4o-mini",
            "anthropic/claude-3.5-sonnet", "anthropic/claude-3-haiku",
            "google/gemini-2.0-flash", "google/gemini-1.5-pro",
            "meta-llama/llama-3.3-70b-instruct", "mistralai/mistral-large",
            "qwen/qwen-2.5-72b-instruct", "deepseek/deepseek-chat",
        ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key, base_url="https://openrouter.ai/api/v1")

    def send_message(self, messages: list[dict], stream: bool = False) -> Generator[str, None, None] | str:
        if not self.client:
            self.client = OpenAI(api_key=self.api_key, base_url="https://openrouter.ai/api/v1")
        formatted = self.format_messages(messages)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=formatted,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            stream=stream,
        )
        if stream:
            def gen():
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            return gen()
        return response.choices[0].message.content or ""
