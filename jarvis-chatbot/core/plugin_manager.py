import json
import os
from typing import Any


PLUGINS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "plugins")


class CustomPlugin:
    def __init__(self, name: str, description: str, command: str, params: list[dict] | None = None):
        self.name = name
        self.description = description
        self.command = command
        self.params = params or []

    def execute(self, **kwargs) -> str:
        import shlex
        import subprocess
        try:
            cmd_parts = shlex.split(self.command, posix=False)
            cmd_parts = [part.format(**{p["name"]: str(kwargs.get(p["name"], "")) for p in self.params}) for part in cmd_parts]
            result = subprocess.run(cmd_parts, capture_output=True, text=True, timeout=30)
            return (result.stdout or result.stderr)[:3000]
        except Exception as e:
            return f"Erro no plugin '{self.name}': {e}"


class PluginManager:
    def __init__(self):
        self.plugins: dict[str, CustomPlugin] = {}
        os.makedirs(PLUGINS_DIR, exist_ok=True)
        self._load_plugins()

    def _load_plugins(self):
        if not os.path.isdir(PLUGINS_DIR):
            return
        for fname in os.listdir(PLUGINS_DIR):
            if fname.endswith(".json"):
                try:
                    with open(os.path.join(PLUGINS_DIR, fname), "r", encoding="utf-8") as f:
                        data = json.load(f)
                    for item in data.get("tools", []):
                        plugin = CustomPlugin(
                            name=item["name"],
                            description=item.get("description", ""),
                            command=item["command"],
                            params=item.get("params", []),
                        )
                        self.plugins[plugin.name] = plugin
                except Exception as e:
                    print(f"Erro ao carregar plugin {fname}: {e}")

    def get_plugin(self, name: str) -> CustomPlugin | None:
        return self.plugins.get(name)

    def get_all(self) -> list[CustomPlugin]:
        return list(self.plugins.values())

    def get_descriptions(self) -> str:
        return "\n".join(f"- {p.name}: {p.description}" for p in self.plugins.values())

    def save_example(self):
        example = {
            "tools": [
                {
                    "name": "ping",
                    "description": "Pinga um endereço",
                    "command": "ping -n 3 {endereco}",
                    "params": [{"name": "endereco", "type": "string", "description": "IP ou hostname"}]
                },
                {
                    "name": "ip_config",
                    "description": "Mostra configuração de rede",
                    "command": "ipconfig"
                }
            ]
        }
        path = os.path.join(PLUGINS_DIR, "exemplo.json")
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(example, f, ensure_ascii=False, indent=2)
