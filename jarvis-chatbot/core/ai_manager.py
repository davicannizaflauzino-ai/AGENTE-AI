import json
import logging
from typing import Optional

from .providers.base import AIProvider
from .providers.openai_provider import OpenAIProvider
from .providers.anthropic_provider import AnthropicProvider
from .providers.google_provider import GoogleProvider
from .providers.ollama_provider import OllamaProvider
from .providers.openrouter_provider import OpenRouterProvider
from .providers.custom_provider import CustomProvider
from .secure_config import (
    load_config,
    dump_config,
    encrypt_config_providers,
    decrypt_config_providers,
)

logger = logging.getLogger(__name__)

BUILTIN_PROVIDERS = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "google": GoogleProvider,
    "ollama": OllamaProvider,
    "openrouter": OpenRouterProvider,
}


class AIManager:
    def __init__(self):
        self.providers: dict[str, AIProvider] = {}
        self._custom_classes: dict[str, type] = {}
        self.current_provider: Optional[str] = None
        self._register_builtin()
        self.load_config()

    def _register_builtin(self):
        self._provider_classes = dict(BUILTIN_PROVIDERS)

    def register_custom_provider(self, key: str, name: str, base_url: str, api_key: str = "", model: str = ""):
        """Registra um provider customizado (qualquer API OpenAI-compatible)."""
        def factory(**kw):
            kw["custom_name"] = name
            kw["base_url"] = base_url
            return CustomProvider(**kw)
        self._custom_classes[key] = factory
        self._provider_classes[key] = factory
        if api_key:
            self.configure_provider(key, api_key=api_key, model=model, base_url=base_url, custom_name=name)
        logger.info("Provider custom registrado: %s (%s)", name, base_url)

    def remove_custom_provider(self, key: str):
        """Remove um provider customizado."""
        self._custom_classes.pop(key, None)
        self._provider_classes.pop(key, None)
        self.providers.pop(key, None)
        if self.current_provider == key:
            self.current_provider = None
        self.save_config()
        logger.info("Provider custom removido: %s", key)

    def get_custom_providers_config(self) -> dict:
        """Retorna configuração dos providers customizados para salvar."""
        config = {}
        for key in self._custom_classes:
            provider = self.providers.get(key)
            if provider:
                config[key] = {
                    "name": getattr(provider, "custom_name", key),
                    "base_url": getattr(provider, "base_url", ""),
                    "api_key": provider.api_key,
                    "model": provider.model,
                }
        return config

    def load_custom_providers_config(self, config: dict):
        """Carrega providers customizados da configuração."""
        for key, cfg in config.items():
            self.register_custom_provider(
                key=key,
                name=cfg.get("name", key),
                base_url=cfg.get("base_url", ""),
                api_key=cfg.get("api_key", ""),
                model=cfg.get("model", ""),
            )

    def get_provider_names(self) -> list[str]:
        return list(self._provider_classes.keys())

    def get_display_names(self) -> dict[str, str]:
        names = {
            "openai": "OpenAI",
            "anthropic": "Anthropic (Claude)",
            "google": "Google Gemini",
            "ollama": "Ollama (Local)",
            "openrouter": "OpenRouter",
        }
        for key, provider in self.providers.items():
            if key in self._custom_classes:
                names[key] = getattr(provider, "custom_name", key)
        return names

    def configure_provider(self, provider_key: str, api_key: str = "", model: str = "", **kwargs):
        cls = self._provider_classes.get(provider_key)
        if not cls:
            raise ValueError(f"Provider '{provider_key}' não encontrado")
        if provider_key in self._custom_classes:
            existing = self.providers.get(provider_key)
            if existing:
                if api_key:
                    existing.api_key = api_key
                if model:
                    existing.model = model
                if "base_url" in kwargs:
                    existing.base_url = kwargs["base_url"]
                if "custom_name" in kwargs:
                    existing.custom_name = kwargs["custom_name"]
                if api_key:
                    from openai import OpenAI
                    existing.client = OpenAI(api_key=existing.api_key, base_url=existing.base_url)
            else:
                provider = cls(api_key=api_key, model=model, **kwargs)
                self.providers[provider_key] = provider
        else:
            provider = cls(api_key=api_key, model=model, **kwargs)
            self.providers[provider_key] = provider
        self.save_config()

    def get_provider(self, provider_key: Optional[str] = None) -> Optional[AIProvider]:
        key = provider_key or self.current_provider
        if key and key in self.providers:
            return self.providers[key]
        return None

    def set_current_provider(self, provider_key: str):
        if provider_key in self.providers:
            self.current_provider = provider_key
            self.save_config()

    def get_available_models(self, provider_key: str) -> list[str]:
        provider = self.providers.get(provider_key)
        if provider:
            return provider.available_models
        cls = self._provider_classes.get(provider_key)
        if cls:
            try:
                return cls().available_models
            except Exception:
                return []
        return []

    def save_config(self):
        providers_data = {}
        for key, provider in self.providers.items():
            providers_data[key] = {
                "api_key": provider.api_key,
                "model": provider.model,
                "max_tokens": provider.max_tokens,
                "temperature": provider.temperature,
                "system_prompt": provider.system_prompt,
            }
            if isinstance(provider, OllamaProvider):
                providers_data[key]["base_url"] = provider.base_url
            if key in self._custom_classes:
                providers_data[key]["_custom"] = True
                providers_data[key]["name"] = getattr(provider, "custom_name", key)
                providers_data[key]["base_url"] = getattr(provider, "base_url", "")

        config = {
            "current_provider": self.current_provider,
            "providers": encrypt_config_providers(providers_data),
        }
        dump_config(config)
        logger.info("Configuração salva com %d providers", len(providers_data))

    def load_config(self):
        config = load_config()
        if not config:
            return
        try:
            providers_data = decrypt_config_providers(config.get("providers", {}))
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning("Erro ao decriptar configuração dos providers: %s", e)
            return
        for key, cfg in providers_data.items():
            if cfg.get("_custom"):
                name = cfg.pop("name", key)
                base_url = cfg.pop("base_url", "")
                self.register_custom_provider(key, name, base_url, cfg.get("api_key", ""), cfg.get("model", ""))
            else:
                self.configure_provider(key, **cfg)
        self.current_provider = config.get("current_provider", "")
        logger.info("Configuração carregada com %d providers", len(providers_data))

    def send_message(self, messages: list[dict], stream: bool = False, provider_key: Optional[str] = None):
        provider = self.get_provider(provider_key)
        if not provider:
            raise ValueError("Nenhum provider configurado. Configure uma API key primeiro.")
        return provider.send_message(messages, stream=stream)