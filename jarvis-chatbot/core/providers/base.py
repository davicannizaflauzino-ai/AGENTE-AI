"""Classe base abstrata para provedores de IA."""

from abc import ABC, abstractmethod
from typing import Generator, Optional


class AIProvider(ABC):
    """Classe base para integração com APIs de IA.

    Cada provedor (OpenAI, Anthropic, etc.) herda desta classe
    e implementa os métodos abstratos.
    """

    def __init__(self, api_key: str = "", model: str = "", **kwargs):
        self.api_key = api_key
        self.model = model or self.default_model
        self.max_tokens = kwargs.get("max_tokens", 4096)
        self.temperature = kwargs.get("temperature", 0.7)
        self.system_prompt = kwargs.get("system_prompt", "")
        self.client = None

    @property
    @abstractmethod
    def name(self) -> str:
        """Nome legível do provedor (ex: 'OpenAI')."""

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Modelo padrão usado quando nenhum é especificado."""

    @property
    @abstractmethod
    def available_models(self) -> list[str]:
        """Lista de modelos disponíveis para este provedor."""

    def get_context_limit(self, model: str = "") -> int:
        """Retorna o limite de contexto (tokens) para o modelo especificado."""
        model = model or self.model
        return self._model_context_map().get(model, self._default_context_limit())

    def _default_context_limit(self) -> int:
        return 128000

    def _model_context_map(self) -> dict[str, int]:
        return {}

    @abstractmethod
    def send_message(self, messages: list[dict], stream: bool = False) -> Generator[str, None, None] | str:
        """Envia mensagens para a API e retorna a resposta.

        Args:
            messages: Lista de dicionários com 'role' e 'content'.
            stream: Se True, retorna um gerador de chunks.

        Returns:
            String com a resposta completa ou gerador de chunks.
        """

    def format_messages(self, messages: list[dict]) -> list[dict]:
        """Formata as mensagens incluindo o system prompt se definido."""
        formatted = []
        if self.system_prompt:
            formatted.append({"role": "system", "content": self.system_prompt})
        formatted.extend(messages)
        return formatted

    def update(self, **kwargs):
        """Atualiza atributos do provider dinamicamente."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def validate_key(self) -> bool:
        """Verifica se a API key parece válida."""
        return bool(self.api_key) and len(self.api_key) > 10

    def _ensure_client(self, client_factory, *args, **kwargs):
        """Garante que o cliente HTTP está inicializado."""
        if self.client is None and self.api_key:
            self.client = client_factory(*args, **kwargs)
        return self.client