import platform
import subprocess
import sys
from .base_tool import BaseTool


class SystemInfoTool(BaseTool):
    @property
    def name(self) -> str:
        return "info_sistema"

    @property
    def description(self) -> str:
        return "Retorna informações do sistema (SO, CPU, memória)"

    def execute(self, **kwargs) -> str:
        info = [
            f"Sistema: {platform.system()} {platform.release()}",
            f"Versão: {platform.version()}",
            f"Máquina: {platform.machine()}",
            f"Processador: {platform.processor()}",
            f"Hostname: {platform.node()}",
        ]
        return "\n".join(info)


class VolumeControlTool(BaseTool):
    @property
    def name(self) -> str:
        return "controle_volume"

    @property
    def description(self) -> str:
        return "Controla volume do sistema (0-100). Parâmetros: nivel (level, 0-100)"

    def execute(self, **kwargs) -> str:
        level = kwargs.get("nivel", "") or kwargs.get("level", "")
        if not level:
            return "Informe o nível de volume (0-100). Ex: nivel=50"
        if sys.platform != "win32":
            return "Controle de volume disponível apenas no Windows"
        try:
            level = max(0, min(100, int(level)))
            vol = int(level * 65535 / 100)
            import ctypes
            ctypes.windll.winmm.waveOutSetVolume(0, vol | (vol << 16))
            return f"Volume ajustado para {level}%"
        except Exception as e:
            return f"Erro ao ajustar volume: {e}"


class ShutdownTool(BaseTool):
    @property
    def name(self) -> str:
        return "desligar"

    @property
    def description(self) -> str:
        return "Desliga ou reinicia o PC. Parâmetro: acao ('desligar' ou 'reiniciar')"

    @property
    def confirmation_required(self) -> bool:
        return True

    def execute(self, **kwargs) -> str:
        acao = kwargs.get("acao", "").lower()
        if acao == "desligar":
            subprocess.run(["shutdown", "/s", "/t", "10"])
            return "Desligando em 10 segundos..."
        elif acao == "reiniciar":
            subprocess.run(["shutdown", "/r", "/t", "10"])
            return "Reiniciando em 10 segundos..."
        return "Ação inválida. Use 'desligar' ou 'reiniciar'"
