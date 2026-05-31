"""Provedor customizado - qualquer API compatível com OpenAI."""

from typing import Generator
import requests
from openai import OpenAI
from .base import AIProvider


class CustomProvider(AIProvider):
    """Provider genérico para qualquer API compatível com OpenAI.

    Permite conectar a DeepSeek, Mistral, Groq, Together AI,
    Perplexity, e qualquer outro endpoint OpenAI-compatible.
    """

    def __init__(self, **kwargs):
        self.custom_name = kwargs.pop("custom_name", "Custom")
        self.base_url = kwargs.pop("base_url", "https://api.openai.com/v1")
        super().__init__(**kwargs)
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    @property
    def name(self) -> str:
        return self.custom_name

    @property
    def default_model(self) -> str:
        return ""

    @property
    def available_models(self) -> list[str]:
        models = []
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            url = self.base_url.rstrip("/") + "/models"
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.ok:
                data = resp.json()
                for m in data.get("data", []):
                    mid = m.get("id", "")
                    if mid and not mid.startswith("ft:"):
                        models.append(mid)
            return models or [self.model] if self.model else ["gpt-4o-mini"]
        except Exception:
            return [self.model] if self.model else ["gpt-4o-mini"]

    def send_message(self, messages: list[dict], stream: bool = False) -> Generator[str, None, None] | str:
        if not self.client:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        formatted = self.format_messages(messages)
        kwargs = dict(model=self.model, messages=formatted, stream=stream)
        kwargs["max_tokens"] = self.max_tokens
        kwargs["temperature"] = self.temperature

        response = self.client.chat.completions.create(**kwargs)
        if stream:
            def gen():
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            return gen()
        return response.choices[0].message.content or ""