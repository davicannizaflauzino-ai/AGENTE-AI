"""Agente de chat simples - modo conversação padrão."""

from typing import Generator
from .base_agent import BaseAgent


class ChatAgent(BaseAgent):
    """Agente de chat padrão. Apenas conversa, sem executar ferramentas."""

    def __init__(self, ai_manager, conversation):
        super().__init__(ai_manager, conversation)
        self.system_prompt = "Você é um assistente AI amigável e prestativo. Responda de forma clara e concisa."

    def process_message(self, user_input: str) -> str:
        self.conversation.add_message("user", user_input)
        messages = self.get_messages()
        response = self.ai.send_message(messages, stream=False)
        self.conversation.add_message("assistant", response)
        return response

    def process_message_stream(self, user_input: str) -> Generator[str, None, None]:
        self.conversation.add_message("user", user_input)
        yield from super().process_message_stream(user_input)