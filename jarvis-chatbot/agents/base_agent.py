"""Classe base abstrata para agentes de conversação."""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Generator
from core.ai_manager import AIManager
from core.conversation import ConversationManager

logger = logging.getLogger(__name__)

_CHARS_PER_TOKEN = 4
_DEFAULT_MAX_CONTEXT_TOKENS = 128000


def _estimate_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except ImportError:
        return len(text) // _CHARS_PER_TOKEN


def _count_tokens(messages: list[dict]) -> int:
    total = 0
    for msg in messages:
        total += _estimate_tokens(msg.get("content", ""))
        total += 4
    total += 8
    return total


def _truncate_messages(messages: list[dict], max_tokens: int) -> list[dict]:
    if _count_tokens(messages) <= max_tokens:
        return messages
    system = None
    if messages and messages[0].get("role") == "system":
        system = messages[0]
        messages = messages[1:]
    while messages and _count_tokens((system or []) + messages) > max_tokens:
        dropped = messages.pop(0)
        logger.debug("Contexto excedido, removendo mensagem antiga: %s...", dropped.get("content", "")[:40])
    if system:
        messages.insert(0, system)
    return messages


class BaseAgent(ABC):
    """Agente base que gerencia o fluxo de mensagens com a IA.

    Subclasses devem implementar process_message() para personalizar
    o comportamento antes/depois de enviar para a API.
    """

    def __init__(self, ai_manager: AIManager, conversation: ConversationManager):
        self.ai = ai_manager
        self.conversation = conversation
        self.system_prompt = ""

    @abstractmethod
    def process_message(self, user_input: str) -> str:
        """Processa uma mensagem do usuário e retorna a resposta."""

    def process_message_stream(self, user_input: str) -> Generator[str, None, None]:
        """Processa mensagem em streaming, gerando chunks da resposta."""
        messages = self.get_messages()
        stream_gen = self.ai.send_message(messages, stream=True)
        full_response = ""
        for chunk in stream_gen:
            if chunk:
                full_response += chunk
                yield chunk
        self.conversation.add_message("assistant", full_response)

    def _get_context_limit(self) -> int:
        provider = self.ai.get_provider()
        if provider:
            return provider.get_context_limit()
        return _DEFAULT_MAX_CONTEXT_TOKENS

    def get_messages(self) -> list[dict]:
        if self.conversation.current_id is None:
            self.conversation.new_conversation()
        msgs = self.conversation.get_messages(self.conversation.current_id)
        if self.system_prompt:
            msgs = [{"role": "system", "content": self.system_prompt}] + msgs
        return _truncate_messages(msgs, self._get_context_limit())

    def clear_context(self):
        """Limpa o contexto atual e inicia nova conversa."""
        self.conversation.new_conversation()