import os
import shlex
import subprocess
import sys
from .base_tool import BaseTool


class RunCommandTool(BaseTool):
    @property
    def name(self) -> str:
        return "executar_comando"

    @property
    def description(self) -> str:
        return "Executa um comando no terminal. Parâmetros: comando (command)"

    @property
    def confirmation_required(self) -> bool:
        return True

    def execute(self, **kwargs) -> str:
        command = kwargs.get("comando", "") or kwargs.get("command", "")
        if not command:
            return "Erro: comando não fornecido"
        try:
            args = shlex.split(command, posix=False)
            result = subprocess.run(
                args, capture_output=True, text=True, timeout=30
            )
            output = result.stdout or result.stderr
            return output[:3000] if output else "Comando executado (sem saída)"
        except subprocess.TimeoutExpired:
            return "Erro: comando excedeu o tempo limite (30s)"
        except Exception as e:
            return f"Erro ao executar comando: {e}"


class OpenAppTool(BaseTool):
    @property
    def name(self) -> str:
        return "abrir_app"

    @property
    def description(self) -> str:
        return "Abre um aplicativo ou arquivo. Parâmetros: caminho (path) ou nome (name)"

    def execute(self, **kwargs) -> str:
        path = kwargs.get("caminho", "") or kwargs.get("path", "") or kwargs.get("nome", "")
        if not path:
            return "Erro: caminho não fornecido"
        safe_path = path.strip().strip("\"'")
        resolved = os.path.abspath(os.path.normpath(safe_path))
        if ".." in path.split(os.sep) or ".." in path.split("/"):
            return "Erro: caminho inválido (.. não permitido)"
        try:
            os.startfile(resolved)
            return f"Aplicativo aberto: {safe_path}"
        except Exception as e:
            return f"Erro ao abrir: {e}"
