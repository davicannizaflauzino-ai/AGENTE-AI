"""Provedor Google - integração com a API Gemini."""

from typing import Generator
from google import genai
from google.genai import types
from .base import AIProvider


class GoogleProvider(AIProvider):
    @property
    def name(self) -> str:
        return "Google Gemini"

    @property
    def default_model(self) -> str:
        return "gemini-2.0-flash"

    @property
    def available_models(self) -> list[str]:
        return ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.5-pro-preview-03-25"]

    def _model_context_map(self) -> dict[str, int]:
        return {
            "gemini-2.0-flash": 1048576,
            "gemini-2.0-flash-lite": 1048576,
            "gemini-1.5-pro": 2097152,
            "gemini-1.5-flash": 1048576,
            "gemini-2.5-pro-preview-03-25": 1048576,
        }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)

    def send_message(self, messages: list[dict], stream: bool = False) -> Generator[str, None, None] | str:
        self._ensure_client(genai.Client, api_key=self.api_key)

        sys_inst = ""
        history = []
        for msg in messages:
            if msg["role"] == "system":
                sys_inst = msg["content"]
            else:
                role = "user" if msg["role"] == "user" else "model"
                history.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))

        config = types.GenerateContentConfig(
            max_output_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        if sys_inst:
            config.system_instruction = sys_inst

        if stream:
            response = self.client.models.generate_content_stream(
                model=self.model, contents=history, config=config
            )
            def gen():
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
            return gen()

        response = self.client.models.generate_content(
            model=self.model, contents=history, config=config
        )
        return response.text or ""