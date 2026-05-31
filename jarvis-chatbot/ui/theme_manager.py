import json
import os
import customtkinter as ctk

try:
    import winreg
    _HAS_WINREG = True
except ImportError:
    _HAS_WINREG = False


THEME_PATH = os.path.join(os.path.dirname(__file__), "assets", "theme.json")

DEFAULT_THEMES = {
    "Jarvis (Dark)": {
        "mode": "dark",
        "colors": {
            "bg_primary": "#0d1117",
            "bg_secondary": "#161b22",
            "bg_tertiary": "#1c2333",
            "bg_card": "#21262d",
            "accent": "#00d4ff",
            "accent_hover": "#00b8e6",
            "accent_gradient_start": "#00d4ff",
            "accent_gradient_end": "#0099ff",
            "text_primary": "#f0f6fc",
            "text_secondary": "#8b949e",
            "text_muted": "#6e7681",
            "user_bubble": "#1f2937",
            "user_bubble_accent": "#0055aa",
            "ai_bubble": "#111827",
            "ai_bubble_accent": "#00d4ff",
            "border": "#30363d",
            "border_light": "#21262d",
            "success": "#3fb950",
            "warning": "#d29922",
            "error": "#f85149",
            "shadow": "rgba(0,0,0,0.3)",
            "overlay": "rgba(0,0,0,0.5)",
        }
    },
    "Jarvis (Light)": {
        "mode": "light",
        "colors": {
            "bg_primary": "#f6f8fa",
            "bg_secondary": "#ffffff",
            "bg_tertiary": "#e8ecf0",
            "bg_card": "#f0f2f5",
            "accent": "#0066ff",
            "accent_hover": "#0052cc",
            "accent_gradient_start": "#0066ff",
            "accent_gradient_end": "#0044cc",
            "text_primary": "#1a1a2e",
            "text_secondary": "#656d76",
            "text_muted": "#8b949e",
            "user_bubble": "#d0d7ff",
            "user_bubble_accent": "#0066ff",
            "ai_bubble": "#ffffff",
            "ai_bubble_accent": "#0066ff",
            "border": "#d0d7de",
            "border_light": "#e8ecf0",
            "success": "#1a7f37",
            "warning": "#9a6700",
            "error": "#cf222e",
            "shadow": "rgba(0,0,0,0.08)",
            "overlay": "rgba(0,0,0,0.3)",
        }
    },
    "Nord": {
        "mode": "dark",
        "colors": {
            "bg_primary": "#2e3440",
            "bg_secondary": "#3b4252",
            "bg_tertiary": "#434c5e",
            "bg_card": "#4c566a",
            "accent": "#88c0d0",
            "accent_hover": "#81a1c1",
            "accent_gradient_start": "#88c0d0",
            "accent_gradient_end": "#81a1c1",
            "text_primary": "#eceff4",
            "text_secondary": "#d8dee9",
            "text_muted": "#9ca0b0",
            "user_bubble": "#434c5e",
            "user_bubble_accent": "#5e81ac",
            "ai_bubble": "#3b4252",
            "ai_bubble_accent": "#88c0d0",
            "border": "#4c566a",
            "border_light": "#434c5e",
            "success": "#a3be8c",
            "warning": "#ebcb8b",
            "error": "#bf616a",
            "shadow": "rgba(0,0,0,0.4)",
            "overlay": "rgba(0,0,0,0.5)",
        }
    },
    "Dracula": {
        "mode": "dark",
        "colors": {
            "bg_primary": "#282a36",
            "bg_secondary": "#44475a",
            "bg_tertiary": "#363849",
            "bg_card": "#3d4055",
            "accent": "#bd93f9",
            "accent_hover": "#9980d9",
            "accent_gradient_start": "#bd93f9",
            "accent_gradient_end": "#ff79c6",
            "text_primary": "#f8f8f2",
            "text_secondary": "#c0c0d0",
            "text_muted": "#8b8ba0",
            "user_bubble": "#44475a",
            "user_bubble_accent": "#6272a4",
            "ai_bubble": "#363849",
            "ai_bubble_accent": "#bd93f9",
            "border": "#555770",
            "border_light": "#44475a",
            "success": "#50fa7b",
            "warning": "#ffb86c",
            "error": "#ff5555",
            "shadow": "rgba(0,0,0,0.4)",
            "overlay": "rgba(0,0,0,0.5)",
        }
    },
    "Matrix": {
        "mode": "dark",
        "colors": {
            "bg_primary": "#000800",
            "bg_secondary": "#001100",
            "bg_tertiary": "#001a00",
            "bg_card": "#002200",
            "accent": "#00ff41",
            "accent_hover": "#00cc33",
            "accent_gradient_start": "#00ff41",
            "accent_gradient_end": "#00cc33",
            "text_primary": "#00ff41",
            "text_secondary": "#00bb30",
            "text_muted": "#008822",
            "user_bubble": "#002200",
            "user_bubble_accent": "#00ff41",
            "ai_bubble": "#000800",
            "ai_bubble_accent": "#00ff41",
            "border": "#003300",
            "border_light": "#002200",
            "success": "#00ff41",
            "warning": "#ffff00",
            "error": "#ff0044",
            "shadow": "rgba(0,255,65,0.15)",
            "overlay": "rgba(0,0,0,0.7)",
        }
    },
    "Cyberpunk": {
        "mode": "dark",
        "colors": {
            "bg_primary": "#0a0020",
            "bg_secondary": "#120030",
            "bg_tertiary": "#1a0045",
            "bg_card": "#220055",
            "accent": "#ff00ff",
            "accent_hover": "#cc00cc",
            "accent_gradient_start": "#ff00ff",
            "accent_gradient_end": "#00ffff",
            "text_primary": "#e0e0ff",
            "text_secondary": "#aa88ff",
            "text_muted": "#7766aa",
            "user_bubble": "#2a0055",
            "user_bubble_accent": "#ff00ff",
            "ai_bubble": "#0a0020",
            "ai_bubble_accent": "#00ffff",
            "border": "#440088",
            "border_light": "#330066",
            "success": "#00ff88",
            "warning": "#ffaa00",
            "error": "#ff0044",
            "shadow": "rgba(255,0,255,0.2)",
            "overlay": "rgba(0,0,0,0.6)",
        }
    },
    "Solarized Dark": {
        "mode": "dark",
        "colors": {
            "bg_primary": "#073642",
            "bg_secondary": "#094452",
            "bg_tertiary": "#0b5362",
            "bg_card": "#0d6272",
            "accent": "#268bd2",
            "accent_hover": "#2aa198",
            "accent_gradient_start": "#268bd2",
            "accent_gradient_end": "#2aa198",
            "text_primary": "#fdf6e3",
            "text_secondary": "#93a1a1",
            "text_muted": "#657b83",
            "user_bubble": "#094452",
            "user_bubble_accent": "#268bd2",
            "ai_bubble": "#073642",
            "ai_bubble_accent": "#2aa198",
            "border": "#125e6e",
            "border_light": "#0b5362",
            "success": "#859900",
            "warning": "#b58900",
            "error": "#dc322f",
            "shadow": "rgba(0,0,0,0.4)",
            "overlay": "rgba(0,0,0,0.5)",
        }
    },
    "Tokyo Night": {
        "mode": "dark",
        "colors": {
            "bg_primary": "#1a1b26",
            "bg_secondary": "#24283b",
            "bg_tertiary": "#2f3346",
            "bg_card": "#363b54",
            "accent": "#7aa2f7",
            "accent_hover": "#5a8de2",
            "accent_gradient_start": "#7aa2f7",
            "accent_gradient_end": "#bb9af7",
            "text_primary": "#c0caf5",
            "text_secondary": "#9aa5ce",
            "text_muted": "#6f7bb0",
            "user_bubble": "#2f3346",
            "user_bubble_accent": "#565f89",
            "ai_bubble": "#24283b",
            "ai_bubble_accent": "#7aa2f7",
            "border": "#3b4261",
            "border_light": "#2f3346",
            "success": "#9ece6a",
            "warning": "#e0af68",
            "error": "#f7768e",
            "shadow": "rgba(0,0,0,0.35)",
            "overlay": "rgba(0,0,0,0.55)",
        }
    },
    "Catppuccin Mocha": {
        "mode": "dark",
        "colors": {
            "bg_primary": "#1e1e2e",
            "bg_secondary": "#313244",
            "bg_tertiary": "#45475a",
            "bg_card": "#585b70",
            "accent": "#89b4fa",
            "accent_hover": "#74c7ec",
            "accent_gradient_start": "#89b4fa",
            "accent_gradient_end": "#cba6f7",
            "text_primary": "#cdd6f4",
            "text_secondary": "#a6adc8",
            "text_muted": "#7f849c",
            "user_bubble": "#45475a",
            "user_bubble_accent": "#6c7086",
            "ai_bubble": "#313244",
            "ai_bubble_accent": "#89b4fa",
            "border": "#585b70",
            "border_light": "#45475a",
            "success": "#a6e3a1",
            "warning": "#f9e2af",
            "error": "#f38ba8",
            "shadow": "rgba(0,0,0,0.35)",
            "overlay": "rgba(0,0,0,0.55)",
        }
    },
}


def detect_windows_theme() -> str:
    if not _HAS_WINREG:
        return "dark"
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return "light" if value == 1 else "dark"
    except Exception:
        return "dark"


class ThemeManager:
    def __init__(self):
        self.current_theme = "Jarvis (Dark)"
        self.auto_theme = False
        self.themes = {}
        self._load_themes()

    def _load_themes(self):
        self.themes = dict(DEFAULT_THEMES)
        if os.path.exists(THEME_PATH):
            try:
                with open(THEME_PATH, "r", encoding="utf-8") as f:
                    custom = json.load(f)
                self.themes.update(custom)
            except Exception:
                pass

    def save_themes(self):
        os.makedirs(os.path.dirname(THEME_PATH), exist_ok=True)
        custom = {k: v for k, v in self.themes.items() if k not in DEFAULT_THEMES}
        with open(THEME_PATH, "w", encoding="utf-8") as f:
            json.dump(custom, f, ensure_ascii=False, indent=2)

    def get_theme_names(self) -> list[str]:
        return list(self.themes.keys())

    def get_auto_theme_name(self) -> str:
        system_mode = detect_windows_theme()
        for name, theme in self.themes.items():
            if theme.get("mode") == system_mode:
                return name
        return "Jarvis (Dark)" if system_mode == "dark" else "Jarvis (Light)"

    def apply_theme(self, theme_name: str, widget: ctk.CTk):
        if theme_name not in self.themes:
            theme_name = "Jarvis (Dark)"
        self.current_theme = theme_name
        theme = self.themes[theme_name]
        c = theme["colors"]
        ctk.set_appearance_mode(theme["mode"])
        widget.configure(fg_color=c["bg_primary"])
        return c

    def get_colors(self, theme_name: str = "") -> dict:
        name = theme_name or self.current_theme
        return self.themes.get(name, DEFAULT_THEMES["Jarvis (Dark)"]).get("colors", {})

    def add_custom_theme(self, name: str, theme_data: dict):
        self.themes[name] = theme_data
        self.save_themes()