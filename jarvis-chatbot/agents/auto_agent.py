import json
from typing import Optional
from .base_agent import BaseAgent
from .tools.base_tool import ToolRegistry


TOOL_CATEGORY_MAP = {
    "file_ops": ["ler_arquivo", "escrever_arquivo", "listar_diretorio"],
    "command_exec": ["executar_comando", "abrir_app"],
    "web_search": ["pesquisar_web", "acessar_url"],
    "system_control": ["info_sistema", "controle_volume", "desligar"],
}

def _get_allowed_tool_names(categories: list[str]) -> list[str]:
    names = []
    for cat in categories:
        names.extend(TOOL_CATEGORY_MAP.get(cat, []))
    return names


class AutoAgent(BaseAgent):
    def __init__(self, ai_manager, conversation):
        super().__init__(ai_manager, conversation)
        self.tool_registry = ToolRegistry()
        self.enabled = False
        self.allowed_tools: list[str] = []
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        base = "Você é o JARVIS, um assistente AI proativo e inteligente."
        if not self.enabled:
            base += "\nModo AUTOMÁTICO DESATIVADO: Apenas responda perguntas, não tome iniciativas."
            return base

        tools_desc = self.tool_registry.get_descriptions(self.allowed_tools)
        if tools_desc:
            base += f"\n\nVocê tem acesso às seguintes ferramentas:\n{tools_desc}"
            base += "\n\nPara usar uma ferramenta, responda com EXATAMENTE este formato JSON:"
            base += '\n{"tool": "nome_da_ferramenta", "params": {"param1": "valor1"}}'
            base += "\nDepois do JSON, você pode continuar sua resposta normalmente."
            base += "\n\nREGRAS:"
            base += "\n- Use ferramentas apenas quando necessário para ajudar o usuário"
            base += "\n- Seja proativo: se perceber que pode ajudar, sugira ou execute ações"
            base += "\n- Execute comandos apenas se tiver permissão explícita"
        else:
            base += "\nModo AUTOMÁTICO ATIVO: Seja proativo, sugira ações e insights sem precisar que o usuário peça."
        return base

    def set_auto_mode(self, enabled: bool, allowed_tools: Optional[list[str]] = None):
        self.enabled = enabled
        if allowed_tools is not None:
            self.allowed_tools = allowed_tools
        self.system_prompt = self._build_system_prompt()
        provider = self.ai.get_provider()
        if provider:
            provider.system_prompt = self.system_prompt

    def process_message(self, user_input: str) -> str:
        self.conversation.add_message("user", user_input)
        messages = self.get_messages()
        response = self.ai.send_message(messages, stream=False)
        processed = self._handle_tool_calls(response)
        self.conversation.add_message("assistant", processed)
        return processed

    def _handle_tool_calls(self, response: str) -> str:
        if not self.enabled:
            return response
        tool_calls = self._extract_tool_calls(response)
        if not tool_calls:
            return response
        allowed_names = _get_allowed_tool_names(self.allowed_tools)
        results = []
        for tc in tool_calls:
            tool_name = tc.get("tool", "")
            params = tc.get("params", {})
            tool = self.tool_registry.get(tool_name)
            if tool and tool_name in allowed_names:
                result = self.tool_registry.execute_with_confirm(tool_name, params)
                results.append(f"[{tool_name}] Resultado: {result}")
            else:
                results.append(f"[{tool_name}] Ferramenta não permitida ou não encontrada")
        if results:
            response += "\n\n---\n" + "\n".join(results)
        return response

    def _extract_tool_calls(self, text: str) -> list[dict]:
        calls = []
        i = 0
        while i < len(text):
            idx = text.find('{"tool"', i)
            if idx == -1:
                break
            depth = 0
            start = -1
            for j in range(idx, len(text)):
                ch = text[j]
                if ch == '{':
                    if depth == 0:
                        start = j
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0 and start != -1:
                        try:
                            calls.append(json.loads(text[start:j+1]))
                        except json.JSONDecodeError:
                            pass
                        i = j + 1
                        break
            else:
                i = idx + 1
        return calls