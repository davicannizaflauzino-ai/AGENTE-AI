import customtkinter as ctk
from tkinter import messagebox
from core.ai_manager import AIManager
from ui.theme_manager import ThemeManager


CUSTOM_PROVIDER_PRESETS = {
    "DeepSeek": {"base_url": "https://api.deepseek.com/v1", "models": ["deepseek-chat", "deepseek-reasoner"]},
    "Mistral AI": {"base_url": "https://api.mistral.ai/v1", "models": ["mistral-large-latest", "mistral-small-latest", "open-mistral-nemo"]},
    "Groq": {"base_url": "https://api.groq.com/openai/v1", "models": ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "gemma2-9b-it"]},
    "Together AI": {"base_url": "https://api.together.xyz/v1", "models": ["mistralai/Mixtral-8x22B-Instruct-v0.1", "meta-llama/Llama-3.3-70B-Instruct-Turbo"]},
    "Perplexity": {"base_url": "https://api.perplexity.ai", "models": ["sonar-pro", "sonar"]},
    "xAI (Grok)": {"base_url": "https://api.x.ai/v1", "models": ["grok-beta", "grok-2-1212"]},
    "OpenAI Compatible": {"base_url": "", "models": [""]},
}


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent, ai_manager: AIManager, theme_manager: ThemeManager, colors: dict, on_save):
        super().__init__(parent)
        self.ai_manager = ai_manager
        self.theme_manager = theme_manager
        self.colors = colors
        self.on_save = on_save
        self.result_data = {}
        self._custom_rows: list[dict] = []

        self.title("⚙️  Configurações")
        self.geometry("820x700")
        self.resizable(False, False)
        self.configure(fg_color=colors["bg_primary"])
        self.transient(parent)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_tabs()

    def _build_tabs(self):
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=self.colors["bg_secondary"],
            segmented_button_fg_color=self.colors["bg_tertiary"],
            segmented_button_selected_color=self.colors["accent"],
            segmented_button_selected_hover_color=self.colors["accent_hover"],
            text_color=self.colors["text_primary"],
            segmented_button_unselected_color=self.colors["bg_tertiary"],
            segmented_button_unselected_hover_color=self.colors["bg_card"],
        )
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=20, pady=(20, 12))

        self.tab_providers = self.tabview.add("🔌  Providers")
        self.tab_custom = self.tabview.add("🌐  Custom")
        self.tab_auto = self.tabview.add("🤖  Modo Auto")
        self.tab_theme = self.tabview.add("🎨  Aparência")
        self.tab_audio = self.tabview.add("🔊  Áudio")
        self.tab_plugins = self.tabview.add("🔧  Plugins")
        self.tab_help = self.tabview.add("❓  Ajuda")
        self.tab_about = self.tabview.add("ℹ️  Sobre")

        self._build_providers_tab()
        self._build_custom_tab()
        self._build_auto_tab()
        self._build_theme_tab()
        self._build_audio_tab()
        self._build_plugins_tab()
        self._build_help_tab()
        self._build_about_tab()

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=1, column=0, pady=(0, 20))
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_frame, text="💾  Salvar",
            fg_color=self.colors["accent"],
            hover_color=self.colors["accent_hover"],
            text_color=self.colors["bg_primary"],
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=10, width=180, height=38,
            command=self._save,
        ).grid(row=0, column=0, padx=8)

        ctk.CTkButton(
            btn_frame, text="Cancelar",
            fg_color=self.colors["bg_tertiary"],
            hover_color=self.colors["bg_card"],
            text_color=self.colors["text_primary"],
            font=ctk.CTkFont(size=13),
            corner_radius=10, width=180, height=38,
            command=self.destroy,
        ).grid(row=0, column=1, padx=8)

    def _build_providers_tab(self):
        tab = self.tab_providers
        tab.grid_columnconfigure(1, weight=1)

        frame = ctk.CTkFrame(tab, fg_color="transparent")
        frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(10, 5), padx=10)
        ctk.CTkLabel(
            frame, text="Provedores Padrão",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["accent"],
        ).pack(anchor="w")

        row = 1
        builtin_keys = ["openai", "anthropic", "google", "ollama", "openrouter"]
        display_names = self.ai_manager.get_display_names()
        self.provider_vars = {}

        for pkey in builtin_keys:
            display = display_names.get(pkey, pkey)
            provider = self.ai_manager.get_provider(pkey)
            current_key = provider.api_key if provider else ""
            current_model = provider.model if provider else ""

            card = ctk.CTkFrame(
                tab, fg_color=self.colors["bg_tertiary"],
                corner_radius=10, border_width=1, border_color=self.colors["border_light"],
            )
            card.grid(row=row, column=0, columnspan=2, sticky="ew", pady=4, padx=4)
            card.grid_columnconfigure(1, weight=1)

            header = ctk.CTkFrame(card, fg_color="transparent")
            header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(8, 2), padx=(12, 5))
            header.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                header, text=display,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=self.colors["text_primary"],
            ).grid(row=0, column=0, sticky="w")

            status = ctk.CTkLabel(
                header, text="✅" if current_key else "❌",
                font=ctk.CTkFont(size=12),
                text_color=self.colors["success"] if current_key else self.colors["text_muted"],
            )
            status.grid(row=0, column=1, sticky="e", padx=(0, 12))

            key_var = ctk.StringVar(value=current_key)
            model_var = ctk.StringVar(value=current_model)
            self.provider_vars[pkey] = {"key": key_var, "model": model_var, "status": status}

            ctk.CTkEntry(
                card, textvariable=key_var,
                placeholder_text=f"API Key",
                fg_color=self.colors["bg_secondary"],
                text_color=self.colors["text_primary"],
                placeholder_text_color=self.colors["text_muted"],
                border_color=self.colors["border"],
                corner_radius=8,
                show="*",
            ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 4))

            model_frame = ctk.CTkFrame(card, fg_color="transparent")
            model_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 4))
            model_frame.grid_columnconfigure(0, weight=1)

            ctk.CTkEntry(
                model_frame, textvariable=model_var,
                placeholder_text="Modelo (ex: gpt-4o, vazio = padrão)",
                fg_color=self.colors["bg_secondary"],
                text_color=self.colors["text_primary"],
                placeholder_text_color=self.colors["text_muted"],
                border_color=self.colors["border"],
                corner_radius=8,
            ).grid(row=0, column=0, sticky="ew")

            test_btn = ctk.CTkButton(
                card, text="🔌  Testar",
                width=80, height=24,
                fg_color=self.colors["bg_secondary"],
                hover_color=self.colors["bg_card"],
                text_color=self.colors["text_primary"],
                font=ctk.CTkFont(size=10),
                corner_radius=6,
                command=lambda k=pkey, s=status, v=key_var: self._test_provider(k, s, v),
            )
            test_btn.grid(row=2, column=1, sticky="e", padx=(8, 0), pady=(0, 4))

            if pkey == "ollama":
                base_url_var = ctk.StringVar(value=provider.base_url if provider else "http://localhost:11434")
                self.provider_vars[pkey]["base_url"] = base_url_var
                ctk.CTkEntry(
                    model_frame, textvariable=base_url_var,
                    fg_color=self.colors["bg_secondary"],
                    text_color=self.colors["text_primary"],
                    border_color=self.colors["border"],
                    corner_radius=8,
                ).grid(row=0, column=1, sticky="ew", padx=(8, 0))

            row += 1

    def _build_custom_tab(self):
        tab = self.tab_custom
        tab.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(tab, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(10, 5), padx=10)
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header, text="Provedores Customizados",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["accent"],
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text="Adicione qualquer API compatível com OpenAI (DeepSeek, Mistral, Groq, Together AI, etc.)",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_secondary"],
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        preset_frame = ctk.CTkFrame(tab, fg_color="transparent")
        preset_frame.grid(row=1, column=0, sticky="ew", pady=5, padx=10)
        preset_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            preset_frame, text="Preset:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text_primary"],
        ).grid(row=0, column=0, padx=(0, 8))

        self.preset_var = ctk.StringVar(value="Selecione...")
        preset_combo = ctk.CTkComboBox(
            preset_frame,
            values=list(CUSTOM_PROVIDER_PRESETS.keys()),
            variable=self.preset_var,
            fg_color=self.colors["bg_secondary"],
            text_color=self.colors["text_primary"],
            border_color=self.colors["border"],
            button_color=self.colors["accent"],
            button_hover_color=self.colors["accent_hover"],
            dropdown_fg_color=self.colors["bg_secondary"],
            dropdown_text_color=self.colors["text_primary"],
            dropdown_hover_color=self.colors["bg_tertiary"],
            corner_radius=8,
            width=180,
            command=self._on_preset_selected,
        )
        preset_combo.grid(row=0, column=1, sticky="w")

        # Scrollable area for custom providers
        self.custom_scroll = ctk.CTkScrollableFrame(
            tab, fg_color="transparent",
            corner_radius=0,
        )
        self.custom_scroll.grid(row=2, column=0, sticky="nsew", pady=(8, 0), padx=4)
        self.custom_scroll.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        self.custom_rows = []
        self._load_existing_custom()

        add_btn = ctk.CTkButton(
            tab, text="＋  Adicionar Provider",
            fg_color=self.colors["accent"],
            hover_color=self.colors["accent_hover"],
            text_color=self.colors["bg_primary"],
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=10, height=36,
            command=self._add_custom_row,
        )
        add_btn.grid(row=3, column=0, pady=(8, 4), padx=10, sticky="ew")

    def _on_preset_selected(self, choice):
        preset = CUSTOM_PROVIDER_PRESETS.get(choice)
        if not preset:
            return
        self._add_custom_row(name=choice, base_url=preset["base_url"], model=preset["models"][0])

    def _load_existing_custom(self):
        for key in list(self.ai_manager._custom_classes.keys()):
            provider = self.ai_manager.get_provider(key)
            if provider:
                self._add_custom_row(
                    name=getattr(provider, "custom_name", key),
                    base_url=getattr(provider, "base_url", ""),
                    api_key=provider.api_key,
                    model=provider.model,
                    key=key,
                )

    def _add_custom_row(self, name="", base_url="", api_key="", model="", key=None):
        row_num = len(self.custom_rows)
        custom_key = key or f"custom_{row_num}_{int(__import__('time').time())}"

        card = ctk.CTkFrame(
            self.custom_scroll, fg_color=self.colors["bg_tertiary"],
            corner_radius=10, border_width=1, border_color=self.colors["border_light"],
        )
        card.grid(row=row_num, column=0, sticky="ew", pady=4, padx=4)
        card.grid_columnconfigure(1, weight=1)

        # Header with name and delete
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(6, 2), padx=(12, 5))
        header.grid_columnconfigure(0, weight=1)

        name_var = ctk.StringVar(value=name)
        name_entry = ctk.CTkEntry(
            header, textvariable=name_var,
            placeholder_text="Nome (ex: DeepSeek)",
            fg_color=self.colors["bg_secondary"],
            text_color=self.colors["text_primary"],
            placeholder_text_color=self.colors["text_muted"],
            border_color=self.colors["border"],
            corner_radius=8,
        )
        name_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        def remove():
            card.destroy()
            if custom_key in self.custom_rows:
                self.custom_rows.remove(custom_key)
            self.ai_manager.remove_custom_provider(custom_key)

        del_btn = ctk.CTkButton(
            header, text="✕", width=28, height=28,
            fg_color="transparent",
            hover_color=self.colors["error"],
            text_color=self.colors["text_muted"],
            font=ctk.CTkFont(size=10),
            corner_radius=6,
            command=remove,
        )
        del_btn.grid(row=0, column=1)

        # Base URL
        url_var = ctk.StringVar(value=base_url)
        ctk.CTkEntry(
            card, textvariable=url_var,
            placeholder_text="Base URL (ex: https://api.deepseek.com/v1)",
            fg_color=self.colors["bg_secondary"],
            text_color=self.colors["text_primary"],
            placeholder_text_color=self.colors["text_muted"],
            border_color=self.colors["border"],
            corner_radius=8,
        ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 4))

        # API Key + Model row
        row_frame = ctk.CTkFrame(card, fg_color="transparent")
        row_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 8))
        row_frame.grid_columnconfigure(0, weight=2)
        row_frame.grid_columnconfigure(1, weight=1)

        key_var_row = ctk.StringVar(value=api_key)
        ctk.CTkEntry(
            row_frame, textvariable=key_var_row,
            placeholder_text="API Key",
            fg_color=self.colors["bg_secondary"],
            text_color=self.colors["text_primary"],
            placeholder_text_color=self.colors["text_muted"],
            border_color=self.colors["border"],
            corner_radius=8,
            show="*",
        ).grid(row=0, column=0, sticky="ew", padx=(0, 4))

        model_var_row = ctk.StringVar(value=model)
        ctk.CTkEntry(
            row_frame, textvariable=model_var_row,
            placeholder_text="Modelo",
            fg_color=self.colors["bg_secondary"],
            text_color=self.colors["text_primary"],
            placeholder_text_color=self.colors["text_muted"],
            border_color=self.colors["border"],
            corner_radius=8,
        ).grid(row=0, column=1, sticky="ew", padx=(4, 0))

        row_data = {
            "key": custom_key,
            "card": card,
            "name": name_var,
            "url": url_var,
            "api_key": key_var_row,
            "model": model_var_row,
        }
        self.custom_rows.append(row_data)

        # NOTA: provider NÃO é registrado aqui - só no Save

    def _build_auto_tab(self):
        tab = self.tab_auto
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            tab, text="Modo Automático",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["accent"],
        ).grid(row=0, column=0, pady=(20, 15), padx=20, sticky="w")

        ctk.CTkLabel(
            tab,
            text="Permite que o JARVIS execute ações no seu computador:\n"
                 "ler arquivos, executar comandos, pesquisar na web e controlar o sistema.",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_secondary"],
            wraplength=600, justify="left",
        ).grid(row=1, column=0, pady=(0, 10), padx=20, sticky="w")

        card = ctk.CTkFrame(
            tab, fg_color=self.colors["bg_tertiary"],
            corner_radius=12, border_width=1, border_color=self.colors["border_light"],
        )
        card.grid(row=2, column=0, sticky="ew", pady=5, padx=16)
        card.grid_columnconfigure(0, weight=1)

        self.auto_enabled = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(
            card, text="Ativar Modo Automático (JARVIS)",
            variable=self.auto_enabled,
            fg_color=self.colors["bg_secondary"],
            progress_color=self.colors["accent"],
            button_color=self.colors["accent"],
            text_color=self.colors["text_primary"],
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, pady=(16, 4), padx=16, sticky="w")

        ctk.CTkLabel(
            card, text="Permissões:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text_secondary"],
        ).grid(row=1, column=0, pady=(8, 4), padx=20, sticky="w")

        self.tool_vars = {}
        tools_info = [
            ("file_ops", "📁  Manipular arquivos (ler, escrever, listar)"),
            ("command_exec", "💻  Executar comandos no terminal"),
            ("web_search", "🌐  Pesquisar na web"),
            ("system_control", "⚡  Controlar sistema (volume, desligar)"),
        ]

        for i, (key, label) in enumerate(tools_info):
            var = ctk.BooleanVar(value=False)
            self.tool_vars[key] = var
            ctk.CTkCheckBox(
                card, text=label,
                variable=var,
                fg_color=self.colors["accent"],
                hover_color=self.colors["accent_hover"],
                text_color=self.colors["text_primary"],
                font=ctk.CTkFont(size=12),
                corner_radius=6,
                checkbox_width=18, checkbox_height=18,
            ).grid(row=2 + i, column=0, pady=3, padx=36, sticky="w")

        ctk.CTkLabel(
            card,
            text="⚠️  Ative apenas permissões que você confia.",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_muted"],
            wraplength=500,
        ).grid(row=6, column=0, pady=(12, 16), padx=20, sticky="w")

    def _build_theme_tab(self):
        tab = self.tab_theme
        tab.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            tab, text="Tema Visual",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["accent"],
        ).grid(row=0, column=0, columnspan=2, pady=(20, 15), padx=20, sticky="w")

        card = ctk.CTkFrame(
            tab, fg_color=self.colors["bg_tertiary"],
            corner_radius=12, border_width=1, border_color=self.colors["border_light"],
        )
        card.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5, padx=16)
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card, text="Tema:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.colors["text_primary"],
        ).grid(row=0, column=0, sticky="w", pady=(14, 6), padx=16)

        self.theme_var = ctk.StringVar(value=self.theme_manager.current_theme)
        theme_names = self.theme_manager.get_theme_names()
        self.theme_combo = ctk.CTkComboBox(
            card, values=theme_names,
            variable=self.theme_var,
            fg_color=self.colors["bg_secondary"],
            text_color=self.colors["text_primary"],
            border_color=self.colors["border"],
            button_color=self.colors["accent"],
            button_hover_color=self.colors["accent_hover"],
            dropdown_fg_color=self.colors["bg_secondary"],
            dropdown_text_color=self.colors["text_primary"],
            dropdown_hover_color=self.colors["bg_tertiary"],
            corner_radius=8,
            state="readonly",
            width=220,
        )
        self.theme_combo.grid(row=0, column=1, sticky="w", padx=(0, 16), pady=(14, 6))

        preview_frame = ctk.CTkFrame(
            card, height=60, corner_radius=8,
            fg_color=self.colors["bg_primary"],
            border_width=1, border_color=self.colors["border"],
        )
        preview_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 6))
        preview_frame.grid_columnconfigure((0, 1, 2), weight=1)

        for i, (label, color_key) in enumerate([
            ("Fundo", "bg_primary"),
            ("Card", "bg_card"),
            ("Destaque", "accent"),
        ]):
            swatch = ctk.CTkFrame(
                preview_frame, height=36, corner_radius=6,
                fg_color=self.colors[color_key],
            )
            swatch.grid(row=0, column=i, sticky="ew", padx=4, pady=8)
            swatch.grid_propagate(False)
            ctk.CTkLabel(
                swatch, text=label,
                font=ctk.CTkFont(size=10),
                text_color=self.colors["text_primary"],
            ).place(relx=0.5, rely=0.5, anchor="center")

        self.auto_theme_var = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(
            card, text="🌙  Seguir tema do Windows automaticamente",
            variable=self.auto_theme_var,
            fg_color=self.colors["bg_secondary"],
            progress_color=self.colors["accent"],
            button_color=self.colors["accent"],
            text_color=self.colors["text_primary"],
            font=ctk.CTkFont(size=12),
        ).grid(row=2, column=0, columnspan=2, pady=(4, 4), padx=16, sticky="w")

        ctk.CTkLabel(
            card, text="Tamanho da fonte:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.colors["text_primary"],
        ).grid(row=3, column=0, sticky="w", pady=(10, 14), padx=16)

        self.font_size_var = ctk.StringVar(value="13")
        font_slider = ctk.CTkOptionMenu(
            card, values=["10", "11", "12", "13", "14", "15", "16", "18", "20"],
            variable=self.font_size_var,
            fg_color=self.colors["bg_secondary"],
            text_color=self.colors["text_primary"],
            button_color=self.colors["accent"],
            button_hover_color=self.colors["accent_hover"],
            dropdown_fg_color=self.colors["bg_secondary"],
            dropdown_text_color=self.colors["text_primary"],
            dropdown_hover_color=self.colors["bg_tertiary"],
            corner_radius=8,
            width=80,
        )
        font_slider.grid(row=3, column=1, sticky="w", padx=(0, 16), pady=(10, 14))

    def _build_audio_tab(self):
        tab = self.tab_audio
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            tab, text="Áudio e Notificações",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["accent"],
        ).grid(row=0, column=0, pady=(20, 15), padx=20, sticky="w")

        card = ctk.CTkFrame(
            tab, fg_color=self.colors["bg_tertiary"],
            corner_radius=12, border_width=1, border_color=self.colors["border_light"],
        )
        card.grid(row=1, column=0, sticky="ew", pady=5, padx=16)
        card.grid_columnconfigure(0, weight=1)

        self.sound_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(
            card, text="🔔  Som de notificação ao receber resposta",
            variable=self.sound_var,
            fg_color=self.colors["bg_secondary"],
            progress_color=self.colors["accent"],
            button_color=self.colors["accent"],
            text_color=self.colors["text_primary"],
            font=ctk.CTkFont(size=13),
        ).grid(row=0, column=0, pady=(16, 4), padx=16, sticky="w")

        ctk.CTkLabel(
            card,
            text="Atalhos:  Ctrl+T = liga/desliga TTS  ·  Ctrl+Shift+N = notificação",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_muted"],
        ).grid(row=1, column=0, pady=(8, 16), padx=20, sticky="w")

    def _build_plugins_tab(self):
        tab = self.tab_plugins
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            tab, text="Plugins Customizados",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["accent"],
        ).grid(row=0, column=0, pady=(20, 10), padx=20, sticky="w")

        card = ctk.CTkFrame(
            tab, fg_color=self.colors["bg_tertiary"],
            corner_radius=12, border_width=1, border_color=self.colors["border_light"],
        )
        card.grid(row=1, column=0, sticky="ew", pady=5, padx=16)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text="Crie arquivos .json em data/plugins/ para adicionar ferramentas.\n"
                 "Um arquivo exemplo.json foi criado automaticamente.",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_primary"],
            wraplength=500, justify="left",
        ).grid(row=0, column=0, pady=(14, 8), padx=16, sticky="w")

        plugins = None
        try:
            from core.plugin_manager import PluginManager
            plugins = PluginManager()
        except Exception:
            pass

        if plugins:
            all_plugins = plugins.get_all()
            if all_plugins:
                ctk.CTkLabel(
                    card, text="Plugins carregados:",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=self.colors["text_secondary"],
                ).grid(row=1, column=0, pady=4, padx=20, sticky="w")
                for i, p in enumerate(all_plugins):
                    ctk.CTkLabel(
                        card, text=f"  🔹  {p.name}: {p.description}",
                        font=ctk.CTkFont(size=11),
                        text_color=self.colors["text_secondary"],
                    ).grid(row=2 + i, column=0, pady=1, padx=36, sticky="w")

        ctk.CTkButton(
            card, text="📂  Abrir pasta de plugins",
            fg_color=self.colors["bg_secondary"],
            hover_color=self.colors["bg_card"],
            text_color=self.colors["text_primary"],
            font=ctk.CTkFont(size=12),
            corner_radius=8,
            command=self._open_plugins_folder,
        ).grid(row=10, column=0, pady=(14, 14), padx=16, sticky="w")

    def _open_plugins_folder(self):
        import os
        import subprocess
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "plugins")
        os.makedirs(path, exist_ok=True)
        subprocess.Popen(["explorer", path])

    def _build_help_tab(self):
        tab = self.tab_help
        tab.grid_columnconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent", corner_radius=0)
        scroll.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        scroll.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        help_data = [
            ("🔌  OpenAI", [
                ("Criar conta", "1. Acesse https://platform.openai.com/signup"),
                ("Gerar API Key", "2. Vá em https://platform.openai.com/api-keys"),
                ("Criar key", "3. Clique em '+ Create new secret key'"),
                ("Copiar", "4. Copie a key (começa com sk-...)"),
                ("Modelos", "gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo"),
            ]),
            ("🟣  Anthropic (Claude)", [
                ("Criar conta", "1. Acesse https://console.anthropic.ai/login"),
                ("API Keys", "2. Vá em https://console.anthropic.ai/settings/keys"),
                ("Criar key", "3. Clique em 'Create Key'"),
                ("Copiar", "4. Copie a key (começa com sk-ant-...)"),
                ("Modelos", "claude-sonnet-4, claude-3-5-sonnet, claude-3-5-haiku"),
            ]),
            ("🟢  Google Gemini", [
                ("Criar conta", "1. Acesse https://aistudio.google.com/"),
                ("API Key", "2. Clique em 'Get API Key'"),
                ("Criar key", "3. Clique em 'Create API Key'"),
                ("Copiar", "4. Copie a key"),
                ("Modelos", "gemini-2.0-flash, gemini-1.5-pro, gemini-2.0-flash-lite"),
            ]),
            ("🟠  Ollama (Local - Grátis)", [
                ("Instalar", "1. Acesse https://ollama.com/download"),
                ("Baixar modelo", '2. No terminal: ollama pull llama3'),
                ("Outros", "3. ollama pull mistral, ollama pull phi3, ollama pull gemma2"),
                ("Rodar", "4. O servidor inicia automático ao usar"),
                ("URL", "http://localhost:11434 (padrão)"),
            ]),
            ("🔶  OpenRouter", [
                ("Criar conta", "1. Acesse https://openrouter.ai/signup"),
                ("API Keys", "2. Vá em https://openrouter.ai/keys"),
                ("Criar key", "3. Clique em 'Create Key'"),
                ("Copiar", "4. Copie a key"),
                ("Modelos", "Acesso a 200+ modelos de vários provedores"),
            ]),
            ("🔷  DeepSeek", [
                ("Criar conta", "1. Acesse https://platform.deepseek.com/signup"),
                ("API Keys", "2. Vá em https://platform.deepseek.com/api_keys"),
                ("Criar key", "3. Clique em 'Create API Key'"),
                ("Copiar", "4. Copie a key"),
                ("Base URL", "https://api.deepseek.com/v1"),
                ("Modelos", "deepseek-chat, deepseek-reasoner"),
            ]),
            ("💜  Mistral AI", [
                ("Criar conta", "1. Acesse https://console.mistral.ai/"),
                ("API Keys", "2. Vá em https://console.mistral.ai/api-keys/"),
                ("Criar key", "3. Clique em 'Create new key'"),
                ("Copiar", "4. Copie a key"),
                ("Base URL", "https://api.mistral.ai/v1"),
                ("Modelos", "mistral-large-latest, mistral-small-latest, open-mistral-nemo"),
            ]),
            ("🟢  Groq", [
                ("Criar conta", "1. Acesse https://console.groq.com/login"),
                ("API Keys", "2. Vá em https://console.groq.com/keys"),
                ("Criar key", "3. Clique em 'Create API Key'"),
                ("Copiar", "4. Copie a key"),
                ("Base URL", "https://api.groq.com/openai/v1"),
                ("Modelos", "llama-3.3-70b-versatile, mixtral-8x7b-32768, gemma2-9b-it"),
            ]),
            ("🔴  Together AI", [
                ("Criar conta", "1. Acesse https://api.together.ai/signup"),
                ("API Keys", "2. Vá em https://api.together.ai/settings/api-keys"),
                ("Criar key", "3. Clique em 'Create Key'"),
                ("Copiar", "4. Copie a key"),
                ("Base URL", "https://api.together.xyz/v1"),
                ("Modelos", "meta-llama/Llama-3.3-70B-Instruct-Turbo, mistralai/Mixtral-8x22B-Instruct-v0.1"),
            ]),
            ("🔵  Perplexity", [
                ("Criar conta", "1. Acesse https://www.perplexity.ai/settings/api"),
                ("API Keys", "2. Gere uma API key nas configurações"),
                ("Copiar", "3. Copie a key"),
                ("Base URL", "https://api.perplexity.ai"),
                ("Modelos", "sonar-pro, sonar"),
            ]),
            ("⚫  xAI (Grok)", [
                ("Criar conta", "1. Acesse https://x.ai/api"),
                ("API Keys", "2. Gere uma API key"),
                ("Copiar", "3. Copie a key"),
                ("Base URL", "https://api.x.ai/v1"),
                ("Modelos", "grok-beta, grok-2-1212"),
            ]),
        ]

        row = 0
        for provider_name, steps in help_data:
            card = ctk.CTkFrame(
                scroll, fg_color=self.colors["bg_tertiary"],
                corner_radius=12, border_width=1, border_color=self.colors["border_light"],
            )
            card.grid(row=row, column=0, sticky="ew", pady=4, padx=8)
            card.grid_columnconfigure(0, weight=1)
            row += 1

            ctk.CTkLabel(
                card, text=provider_name,
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color=self.colors["accent"],
            ).grid(row=0, column=0, sticky="w", padx=16, pady=(10, 4))

            for label, detail in steps:
                step_frame = ctk.CTkFrame(card, fg_color="transparent")
                step_frame.grid(row=card.grid_size()[1], column=0, sticky="ew", padx=16, pady=1)
                step_frame.grid_columnconfigure(0, weight=0)
                step_frame.grid_columnconfigure(1, weight=1)

                ctk.CTkLabel(
                    step_frame, text=f"  {label}:",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=self.colors["text_primary"],
                    anchor="w",
                ).grid(row=0, column=0, sticky="w")

                detail_lbl = ctk.CTkLabel(
                    step_frame, text=detail,
                    font=ctk.CTkFont(size=11),
                    text_color=self.colors["text_secondary"],
                    anchor="w", justify="left",
                    wraplength=500,
                )
                detail_lbl.grid(row=0, column=1, sticky="w", padx=(8, 0))

            ctk.CTkLabel(
                card, text="",
                font=ctk.CTkFont(size=4),
            ).grid(row=card.grid_size()[1], column=0)

    def _build_about_tab(self):
        tab = self.tab_about
        tab.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(
            tab, fg_color=self.colors["bg_tertiary"],
            corner_radius=12, border_width=1, border_color=self.colors["border_light"],
        )
        card.grid(row=0, column=0, sticky="ew", pady=(16, 5), padx=16)
        card.grid_columnconfigure(0, weight=1)

        lines = [
            ("🤖  JARVIS AI Chatbot", 20),
            ("", 4),
            ("Versão 2.0.0  ·  Python + CustomTkinter", 11),
            ("", 8),
            ("Recursos:", 13),
            ("  Streaming em tempo real  ·  Syntax Highlight", 11),
            ("  Provedores ilimitados (OpenAI, Anthropic, DeepSeek, Mistral, Groq...)", 11),
            ("  9 temas visuais  ·  Auto-tema Windows", 11),
            ("  Busca no histórico  ·  Exportar conversas", 11),
            ("  TTS  ·  Notificações  ·  Bandeja Windows", 11),
            ("  Plugins customizados  ·  10+ atalhos", 11),
            ("", 8),
            ("Atalhos:", 13),
            ("  Ctrl+N  Nova conversa       Ctrl+E  Exportar", 11),
            ("  Ctrl+T  Toggle TTS           Ctrl+L  Limpar chat", 11),
            ("  Ctrl+M  Minimizar bandeja    Ctrl+,  Settings", 11),
            ("  Ctrl+S  Auto-scroll          Ctrl+W  Deletar", 11),
            ("", 8),
            ("Feito por @opencode  ·  github.com/anomalyco/opencode", 10),
        ]

        for i, (text, size) in enumerate(lines):
            color_key = "accent" if size >= 18 else ("text_secondary" if size <= 10 else "text_primary")
            ctk.CTkLabel(
                card, text=text,
                font=ctk.CTkFont(size=size, weight="bold" if size >= 16 else "normal"),
                text_color=self.colors.get(color_key, self.colors["text_primary"]),
            ).grid(row=i, column=0, pady=0, padx=16, sticky="w")

    def _save(self):
        # Save built-in providers
        for pkey, vars in self.provider_vars.items():
            key = vars["key"].get().strip()
            model = vars["model"].get().strip()
            kwargs = {}
            if "base_url" in vars:
                kwargs["base_url"] = vars["base_url"].get().strip()
            if key:
                self.ai_manager.configure_provider(pkey, api_key=key, model=model or None, **kwargs)
                if not self.ai_manager.current_provider:
                    self.ai_manager.set_current_provider(pkey)

        # Save custom providers
        for row in self.custom_rows:
            name = row["name"].get().strip()
            base_url = row["url"].get().strip()
            api_key = row["api_key"].get().strip()
            model = row["model"].get().strip()
            if name and base_url:
                self.ai_manager.register_custom_provider(
                    key=row["key"], name=name, base_url=base_url,
                    api_key=api_key, model=model,
                )
                if not self.ai_manager.current_provider:
                    self.ai_manager.set_current_provider(row["key"])

        self.ai_manager.save_config()

        self.result_data["theme"] = self.theme_var.get()
        self.result_data["auto_enabled"] = self.auto_enabled.get()
        self.result_data["tools"] = [k for k, v in self.tool_vars.items() if v.get()]
        self.result_data["sound"] = self.sound_var.get()
        self.result_data["auto_theme"] = self.auto_theme_var.get()
        self.result_data["font_size"] = int(self.font_size_var.get())

        self.on_save(self.result_data)
        self.destroy()

    def _test_provider(self, pkey: str, status_label, key_var):
        key = key_var.get().strip()
        if not key:
            status_label.configure(text="❌", text_color=self.colors["text_muted"])
            messagebox.showwarning("Teste", "Digite uma API Key primeiro.")
            return
        status_label.configure(text="⏳", text_color=self.colors["accent"])
        status_label.update()
        try:
            from openai import OpenAI
            base_urls = {
                "openai": "https://api.openai.com/v1",
                "anthropic": "",
                "google": "",
                "ollama": "http://localhost:11434/v1",
                "openrouter": "https://openrouter.ai/api/v1",
            }
            url = base_urls.get(pkey, "")
            if url:
                client = OpenAI(api_key=key, base_url=url)
                client.models.list()
                status_label.configure(text="✅", text_color=self.colors["success"])
                messagebox.showinfo("Teste", f"✅ Conexão OK! API Key válida.")
            else:
                status_label.configure(text="?", text_color=self.colors["text_muted"])
                messagebox.showinfo("Teste", "Teste automático não disponível para este provider.\nSalve e envie uma mensagem para testar.")
        except Exception as e:
            status_label.configure(text="❌", text_color=self.colors["error"])
            messagebox.showerror("Teste", f"Falha na conexão:\n{e}")