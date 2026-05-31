from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        ...

    @property
    def confirmation_required(self) -> bool:
        return False

    @abstractmethod
    def execute(self, **kwargs) -> str:
        ...


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        self._confirm_callback = None

    def set_confirm_callback(self, callback):
        self._confirm_callback = callback

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def get_descriptions(self, allowed: list[str] | None = None) -> str:
        lines = []
        for name, tool in self._tools.items():
            if allowed is None or name in allowed:
                lines.append(f"- {name}: {tool.description}")
        return "\n".join(lines)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def execute_with_confirm(self, tool_name: str, params: dict) -> str:
        tool = self._tools.get(tool_name)
        if not tool:
            return f"[{tool_name}] Ferramenta não encontrada"
        if tool.confirmation_required and self._confirm_callback:
            confirmed = self._confirm_callback(tool_name, params)
            if not confirmed:
                return f"[{tool_name}] Ação cancelada pelo usuário"
        return tool.execute(**params)
