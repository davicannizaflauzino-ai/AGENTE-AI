from typing import Generator
import json
import requests
from .base import AIProvider


class OllamaProvider(AIProvider):
    @property
    def name(self) -> str:
        return "Ollama (Local)"

    @property
    def default_model(self) -> str:
        return "llama3"

    @property
    def available_models(self) -> list[str]:
        models = []
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.ok:
                models = [m["name"] for m in resp.json().get("models", [])]
        except Exception:
            pass
        return models or ["llama3", "mistral", "phi3", "gemma2", "llama2"]

    def __init__(self, **kwargs):
        self.base_url = kwargs.pop("base_url", "http://localhost:11434")
        super().__init__(**kwargs)

    def send_message(self, messages: list[dict], stream: bool = False) -> Generator[str, None, None] | str:
        formatted = self.format_messages(messages)
        payload = {
            "model": self.model,
            "messages": formatted,
            "stream": stream,
            "options": {
                "num_predict": self.max_tokens,
                "temperature": self.temperature,
            }
        }
        resp = requests.post(f"{self.base_url}/api/chat", json=payload, stream=stream, timeout=120)
        resp.raise_for_status()

        if stream:
            def gen():
                for line in resp.iter_lines(decode_unicode=True):
                    if line:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]
            return gen()

        data = resp.json()
        return data.get("message", {}).get("content", "")
