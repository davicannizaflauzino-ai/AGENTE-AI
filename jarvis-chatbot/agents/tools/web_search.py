import requests
from urllib.parse import urlparse
from .base_tool import BaseTool


BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "169.254.169.254"}


def _validate_url(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return "Apenas URLs HTTP/HTTPS são permitidas"
    if parsed.hostname in BLOCKED_HOSTS:
        return "URLs locais não são permitidas"
    if parsed.hostname == "169.254.169.254":
        return "URL bloqueada por segurança"
    for part in parsed.hostname.split("."):
        if part == "local":
            return "URLs .local não são permitidas"
    return None


class WebSearchTool(BaseTool):
    @property
    def name(self) -> str:
        return "pesquisar_web"

    @property
    def description(self) -> str:
        return "Pesquisa na web usando DuckDuckGo. Parâmetro: query (consulta)"

    def execute(self, **kwargs) -> str:
        query = kwargs.get("query", "") or kwargs.get("consulta", "")
        if not query:
            return "Erro: consulta não fornecida"
        try:
            url = f"https://api.duckduckgo.com/?q={requests.utils.quote(query)}&format=json&no_html=1"
            resp = requests.get(url, timeout=15)
            data = resp.json()
            results = []
            if data.get("AbstractText"):
                results.append(f"Resumo: {data['AbstractText']}")
            if data.get("AbstractURL"):
                results.append(f"Fonte: {data['AbstractURL']}")
            for topic in data.get("RelatedTopics", [])[:5]:
                if "Text" in topic:
                    results.append(f"- {topic['Text']}")
            return "\n".join(results) if results else "Nenhum resultado encontrado."
        except Exception as e:
            return f"Erro na pesquisa: {e}"


class FetchURLTool(BaseTool):
    @property
    def name(self) -> str:
        return "acessar_url"

    @property
    def description(self) -> str:
        return "Acessa uma URL e retorna o conteúdo. Parâmetro: url"

    def execute(self, **kwargs) -> str:
        url = kwargs.get("url", "")
        if not url:
            return "Erro: URL não fornecida"
        err = _validate_url(url)
        if err:
            return f"Erro de segurança: {err}"
        try:
            resp = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
            text = resp.text[:5000]
            return text
        except Exception as e:
            return f"Erro ao acessar URL: {e}"
