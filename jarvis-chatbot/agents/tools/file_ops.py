import os
from .base_tool import BaseTool


_PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SENSITIVE_DIRS = [
    os.environ.get("WINDIR", r"C:\Windows"),
    os.environ.get("SystemRoot", r"C:\Windows"),
    os.path.join(_PROJECT_DIR, "data"),
]


def _safe_path(path: str) -> str:
    resolved = os.path.abspath(os.path.normpath(path.strip().strip("\"'")))
    for sensitive in SENSITIVE_DIRS:
        if resolved.lower().startswith(sensitive.lower() + os.sep) or resolved.lower() == sensitive.lower():
            raise PermissionError(f"Acesso negado a diretório do sistema: {sensitive}")
    return resolved


class ReadFileTool(BaseTool):
    @property
    def name(self) -> str:
        return "ler_arquivo"

    @property
    def description(self) -> str:
        return "Lê o conteúdo de um arquivo. Parâmetro: caminho (path)"

    def execute(self, **kwargs) -> str:
        path = kwargs.get("caminho", "")
        if not path:
            return "Erro: caminho não fornecido"
        try:
            resolved = _safe_path(path)
            with open(resolved, "r", encoding="utf-8") as f:
                return f.read()[:5000]
        except PermissionError as e:
            return f"Erro: {e}"
        except Exception as e:
            return f"Erro ao ler arquivo: {e}"


class WriteFileTool(BaseTool):
    @property
    def name(self) -> str:
        return "escrever_arquivo"

    @property
    def description(self) -> str:
        return "Escreve conteúdo em um arquivo. Parâmetros: caminho (path), conteudo (content)"

    def execute(self, **kwargs) -> str:
        path = kwargs.get("caminho", "")
        content = kwargs.get("conteudo", "")
        if not path:
            return "Erro: caminho não fornecido"
        try:
            resolved = _safe_path(path)
            os.makedirs(os.path.dirname(resolved), exist_ok=True)
            with open(resolved, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Arquivo salvo: {resolved}"
        except PermissionError as e:
            return f"Erro: {e}"
        except Exception as e:
            return f"Erro ao escrever arquivo: {e}"


class ListDirTool(BaseTool):
    @property
    def name(self) -> str:
        return "listar_diretorio"

    @property
    def description(self) -> str:
        return "Lista arquivos em um diretório. Parâmetro: caminho (path)"

    def execute(self, **kwargs) -> str:
        path = kwargs.get("caminho", ".")
        try:
            resolved = _safe_path(path)
            items = os.listdir(resolved)
            return "\n".join(items[:50])
        except PermissionError as e:
            return f"Erro: {e}"
        except Exception as e:
            return f"Erro ao listar diretório: {e}"
