import logging
import threading
import queue
import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from core.ai_manager import AIManager
from core.conversation import ConversationManager
from core.plugin_manager import PluginManager
from agents.chat_agent import ChatAgent
from agents.auto_agent import AutoAgent
from agents.tools.file_ops import ReadFileTool, WriteFileTool, ListDirTool
from agents.tools.command_exec import RunCommandTool, OpenAppTool
from agents.tools.web_search import WebSearchTool, FetchURLTool
from agents.tools.system_control import SystemInfoTool, VolumeControlTool, ShutdownTool
from ui.theme_manager import ThemeManager
from ui.components.chat_display import ChatDisplay, StreamingBuffer
from ui.components.input_area import InputArea
from ui.components.sidebar import Sidebar
from ui.components.settings_window import SettingsWindow
from ui.components.tooltip import ToolTip

logger = logging.getLogger(__name__)

try:
    import winsound
    _HAS_SOUND = True
except ImportError:
    _HAS_SOUND = False

try:
    import pyttsx3
    _HAS_TTS = True
except ImportError:
    _HAS_TTS = False

try:
    import pystray
    from PIL import Image
    _HAS_TRAY = True
except ImportError:
    _HAS_TRAY = False


def _play_notification():
    if _HAS_SOUND:
        try:
            winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
        except Exception as e:
            logger.debug("Falha no som de notificação: %s", e)


class JarvisApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        logger.info("Inicializando JARVIS App")

        self.ai_manager = AIManager()
        self.conversation = ConversationManager()
        self.theme_manager = ThemeManager()
        self.plugin_manager = PluginManager()
        self.plugin_manager.save_example()

        self.chat_agent = ChatAgent(self.ai_manager, self.conversation)
        self.auto_agent = AutoAgent(self.ai_manager, self.conversation)
        self.current_agent = self.chat_agent
        self._register_tools()

        self._tts_engine = None
        self._tts_enabled = False
        self._sound_enabled = True
        self._tray_icon = None
        self._stream_buffer: StreamingBuffer | None = None
        self._response_text = ""
        self._loading = False
        self._font_size = 13
        self._stop_event = threading.Event()
        self._mode = "chat"

        self.title("JARVIS - Assistente IA")
        self._load_geometry()
        self.minsize(900, 600)

        self.colors = self.theme_manager.get_colors()
        self.configure(fg_color=self.colors["bg_primary"])

        self._build_ui()
        self._bind_shortcuts()
        self._init_conversation()
        self._try_auto_theme()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Configure>", self._on_window_resize)

    def _load_geometry(self):
        try:
            import json, os
            path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "config.json")
            if os.path.exists(path):
                with open(path, "r") as f:
                    cfg = json.load(f)
                geo = cfg.get("_window_geometry", "")
                if geo:
                    self.geometry(geo)
                    return
        except Exception as e:
            logger.debug("Erro ao carregar geometria: %s", e)
        self.geometry("1200x760")

    def _save_geometry(self):
        try:
            import json, os
            path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "config.json")
            with open(path, "r") as f:
                cfg = json.load(f)
            cfg["_window_geometry"] = self.geometry()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                json.dump(cfg, f, indent=2)
        except Exception as e:
            logger.debug("Erro ao salvar geometria: %s", e)

    def _register_tools(self):
        registry = self.auto_agent.tool_registry
        registry.set_confirm_callback(self._confirm_tool_execution)
        registry.register(ReadFileTool())
        registry.register(WriteFileTool())
        registry.register(ListDirTool())
        registry.register(RunCommandTool())
        registry.register(OpenAppTool())
        registry.register(WebSearchTool())
        registry.register(FetchURLTool())
        registry.register(SystemInfoTool())
        registry.register(VolumeControlTool())
        registry.register(ShutdownTool())

    def _confirm_tool_execution(self, tool_name: str, params: dict) -> bool:
        import queue as _queue
        q = _queue.Queue()
        def ask():
            result = messagebox.askyesno(
                "⚠️  Confirmar Ação",
                f"O JARVIS deseja executar:\n\n"
                f"🔧  {tool_name}\n"
                f"📋  Parâmetros: {params}\n\n"
                f"Permitir esta ação?",
            )
            q.put(result)
        self.after(0, ask)
        return q.get()

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_sidebar()
        self._build_main_area()
        self._build_topbar()

    def _build_topbar(self):
        topbar = ctk.CTkFrame(
            self, fg_color=self.colors["bg_secondary"],
            height=52, corner_radius=0,
            border_width=0,
        )
        topbar.grid(row=0, column=1, sticky="ew")
        topbar.grid_columnconfigure(1, weight=1)
        topbar.grid_propagate(False)

        self.logo_label = ctk.CTkLabel(
            topbar,
            text="  🤖  JARVIS",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["accent"],
        )
        self.logo_label.grid(row=0, column=0, padx=(16, 8), pady=10)

        self.mode_var = ctk.StringVar(value="chat")
        self.mode_selector = ctk.CTkSegmentedButton(
            topbar,
            values=["💬 Chat", "📋 Plan", "🔨 Build"],
            variable=self.mode_var,
            font=ctk.CTkFont(size=11),
            selected_color=self.colors["accent"],
            selected_hover_color=self.colors["accent_hover"],
            unselected_color=self.colors["bg_tertiary"],
            unselected_hover_color=self.colors["bg_card"],
            text_color=self.colors["text_primary"],
            command=self._on_mode_change,
        )
        self.mode_selector.grid(row=0, column=1, padx=4, pady=8)

        self.provider_label = ctk.CTkLabel(
            topbar,
            text="",
            font=ctk.CTkFont(size=10),
            text_color=self.colors["text_muted"],
        )
        self.provider_label.grid(row=0, column=2, padx=(4, 0))

        provider = self.ai_manager.get_provider()
        if provider:
            self._build_model_selector(topbar, provider)

        btn_frame = ctk.CTkFrame(topbar, fg_color="transparent")
        btn_frame.grid(row=0, column=4, padx=(0, 12))

        self.auto_scroll_btn = ctk.CTkButton(
            btn_frame, text="⬇", width=30, height=28,
            fg_color=self.colors["accent"],
            hover_color=self.colors["accent_hover"],
            text_color=self.colors["bg_primary"],
            font=ctk.CTkFont(size=12),
            corner_radius=8,
            command=self._toggle_auto_scroll,
        )
        self.auto_scroll_btn.grid(row=0, column=0, padx=2)
        ToolTip(self.auto_scroll_btn, "Auto-scroll (Ctrl+S)")

        self.tts_btn = ctk.CTkButton(
            btn_frame, text="🔊", width=30, height=28,
            fg_color=self.colors["bg_tertiary"],
            hover_color=self.colors["bg_card"],
            text_color=self.colors["text_secondary"],
            font=ctk.CTkFont(size=12),
            corner_radius=8,
            command=self._toggle_tts,
        )
        self.tts_btn.grid(row=0, column=1, padx=2)
        ToolTip(self.tts_btn, "Ler resposta em voz (Ctrl+T)")

        self.auto_switch = ctk.CTkSwitch(
            btn_frame, text="Auto",
            fg_color=self.colors["bg_tertiary"],
            progress_color=self.colors["accent"],
            button_color=self.colors["accent"],
            text_color=self.colors["text_secondary"],
            font=ctk.CTkFont(size=11),
            command=self._toggle_auto_mode,
        )
        self.auto_switch.grid(row=0, column=2, padx=6)

        settings_btn = ctk.CTkButton(
            btn_frame, text="⚙️", width=30, height=28,
            fg_color=self.colors["bg_tertiary"],
            hover_color=self.colors["bg_card"],
            text_color=self.colors["text_primary"],
            font=ctk.CTkFont(size=14),
            corner_radius=8,
            command=self._open_settings,
        )
        settings_btn.grid(row=0, column=3, padx=2)
        ToolTip(settings_btn, "Configurações (Ctrl+,)")

        export_btn = ctk.CTkButton(
            btn_frame, text="📥", width=30, height=28,
            fg_color=self.colors["bg_tertiary"],
            hover_color=self.colors["bg_card"],
            text_color=self.colors["text_primary"],
            font=ctk.CTkFont(size=14),
            corner_radius=8,
            command=self._export_conversation,
        )
        export_btn.grid(row=0, column=4, padx=2)
        ToolTip(export_btn, "Exportar conversa (Ctrl+E)")

        self.regenerate_btn = ctk.CTkButton(
            btn_frame, text="🔄", width=30, height=28,
            fg_color=self.colors["bg_tertiary"],
            hover_color=self.colors["bg_card"],
            text_color=self.colors["text_primary"],
            font=ctk.CTkFont(size=14),
            corner_radius=8,
            command=self._regenerate_last,
        )
        self.regenerate_btn.grid(row=0, column=5, padx=2)
        ToolTip(self.regenerate_btn, "Regenerar última resposta")
        self.regenerate_btn.configure(state="disabled")

        clear_btn = ctk.CTkButton(
            btn_frame, text="🗑️", width=30, height=28,
            fg_color=self.colors["bg_tertiary"],
            hover_color=self.colors["error"],
            text_color=self.colors["text_primary"],
            font=ctk.CTkFont(size=14),
            corner_radius=8,
            command=self._clear_chat,
        )
        clear_btn.grid(row=0, column=6, padx=2)
        ToolTip(clear_btn, "Nova conversa (Ctrl+L)")

    def _build_model_selector(self, parent, provider):
        models = provider.available_models
        self.model_var = ctk.StringVar(value=provider.model or models[0] if models else "")
        self.model_combo = ctk.CTkComboBox(
            parent, values=models,
            variable=self.model_var,
            width=140, height=28,
            fg_color=self.colors["bg_tertiary"],
            text_color=self.colors["text_primary"],
            border_color=self.colors["border"],
            button_color=self.colors["accent"],
            button_hover_color=self.colors["accent_hover"],
            dropdown_fg_color=self.colors["bg_secondary"],
            dropdown_text_color=self.colors["text_primary"],
            dropdown_hover_color=self.colors["bg_tertiary"],
            corner_radius=8,
            font=ctk.CTkFont(size=10),
            command=self._on_model_change,
        )
        self.model_combo.grid(row=0, column=3, padx=(0, 8))

    def _on_model_change(self, choice):
        provider = self.ai_manager.get_provider()
        if provider:
            provider.model = choice
            self.ai_manager.save_config()
            self._update_provider_label()

    def _toggle_auto_scroll(self):
        enabled = self.chat_display.toggle_auto_scroll()
        self.auto_scroll_btn.configure(
            fg_color=self.colors["accent"] if enabled else self.colors["bg_tertiary"],
            text_color=self.colors["bg_primary"] if enabled else self.colors["text_secondary"],
        )

    def _update_provider_label(self):
        provider = self.ai_manager.get_provider()
        if provider:
            self.provider_label.configure(text=f"⚡ {provider.name}")
            if hasattr(self, 'model_var') and provider.model:
                self.model_var.set(provider.model)
        else:
            self.provider_label.configure(text="")

    def _build_sidebar(self):
        self.sidebar = Sidebar(
            self, self.colors,
            conv_callback=self._load_conversation,
            delete_callback=self._delete_conversation,
        )
        self.sidebar.grid(row=0, column=0, sticky="ns", rowspan=3)
        self.sidebar.set_search_callback(self._on_search)
        self.sidebar.set_pin_callback(self._on_pin_conversation)

    def _build_main_area(self):
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=1, column=1, sticky="nsew", padx=0, pady=0)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(0, weight=1)

        inner = ctk.CTkFrame(main, fg_color="transparent")
        inner.grid(row=0, column=0, sticky="nsew", padx=12, pady=(4, 0))
        inner.grid_columnconfigure(0, weight=1)
        inner.grid_rowconfigure(0, weight=1)

        self.chat_display = ChatDisplay(inner, self.colors)
        self.chat_display.grid(row=0, column=0, sticky="nsew")

        bottom_frame = ctk.CTkFrame(main, fg_color="transparent")
        bottom_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(4, 12))
        bottom_frame.grid_columnconfigure(0, weight=1)

        self.input_area = InputArea(bottom_frame, self.colors, send_callback=self._send_message, stop_callback=self._stop_streaming)
        self.input_area.grid(row=0, column=0, sticky="ew")

    def _on_window_resize(self, event):
        if event.widget == self:
            w = self.winfo_width()
            if w < 1000:
                self.sidebar.configure(width=200)
            else:
                self.sidebar.configure(width=260)

    def _bind_shortcuts(self):
        self.bind("<Control-n>", lambda e: self._new_conversation())
        self.bind("<Control-w>", lambda e: self._delete_current_conversation())
        self.bind("<Control-,>", lambda e: self._open_settings())
        self.bind("<Control-l>", lambda e: self._clear_chat())
        self.bind("<Control-e>", lambda e: self._export_conversation())
        self.bind("<Control-t>", lambda e: self._toggle_tts())
        self.bind("<Control-m>", lambda e: self._minimize_to_tray())
        self.bind("<Control-s>", lambda e: self._toggle_auto_scroll())
        self.bind("<Control-f>", lambda e: self.chat_display.show_find())
        self.bind("<Escape>", lambda e: self.chat_display.hide_find())

    def _init_conversation(self):
        convs = self.conversation.get_conversations()
        if convs:
            self._load_conversation(convs[0]["id"])
        else:
            self.conversation.new_conversation()
        self.sidebar.refresh(self.conversation.get_conversations(), self.conversation.current_id)

    def _try_auto_theme(self):
        if self.theme_manager.auto_theme:
            auto_name = self.theme_manager.get_auto_theme_name()
            if auto_name != self.theme_manager.current_theme:
                self.colors = self.theme_manager.get_colors(auto_name)
                self.theme_manager.apply_theme(auto_name, self)
                self._update_theme()

    def _on_mode_change(self, choice):
        mode_map = {"💬 Chat": "chat", "📋 Plan": "plan", "🔨 Build": "build"}
        self._mode = mode_map.get(choice, "chat")
        prompts = {
            "chat": "Você é um assistente AI amigável e prestativo. Responda de forma clara e concisa.",
            "plan": "Você é um assistente AI focado em planejamento.\n\n"
                    "Antes de responder ou executar qualquer ação, apresente um plano detalhado.\n"
                    "Use o formato:\n"
                    "📋 Plano:\n"
                    "1. Primeiro passo\n"
                    "2. Segundo passo\n"
                    "3. Terceiro passo\n\n"
                    "Depois do plano, execute cada passo um de cada vez.\n"
                    "Seja estruturado e lógico.",
            "build": "Você é um assistente AI focado em desenvolvimento de código.\n\n"
                     "Priorize código funcional, bem estruturado e comentado.\n"
                     "Sempre especifique a linguagem nos blocos de código.\n"
                     "Explique a lógica antes de mostrar o código.\n"
                     "Siga boas práticas e padrões de design.",
        }
        self.chat_agent.system_prompt = prompts.get(self._mode, prompts["chat"])
        self.auto_agent.system_prompt = self.auto_agent._build_system_prompt()
        provider = self.ai_manager.get_provider()
        if provider:
            provider.system_prompt = self.chat_agent.system_prompt
        self._add_system_message(f"🔄 Modo {choice} ativado")

    def _toggle_auto_mode(self):
        enabled = bool(self.auto_switch.get())
        if enabled:
            warn = messagebox.askyesno(
                "⚠️  Modo Automático",
                "No modo automático, o JARVIS pode:\n\n"
                "• Executar comandos no terminal\n"
                "• Ler e escrever arquivos\n"
                "• Controlar o sistema (volume, desligar)\n"
                "• Pesquisar na web\n\n"
                "Apenas ferramentas com permissão explícita serão usadas.\n"
                "Continuar?",
            )
            if not warn:
                self.auto_switch.deselect()
                return
        self.auto_agent.set_auto_mode(enabled, self.auto_agent.allowed_tools)
        self.current_agent = self.auto_agent if enabled else self.chat_agent
        self._add_system_message(f"Modo {'Automático' if enabled else 'Chat'} ativado")

    def _toggle_tts(self):
        self._tts_enabled = not self._tts_enabled
        self.tts_btn.configure(
            fg_color=self.colors["accent"] if self._tts_enabled else self.colors["bg_tertiary"],
            text_color=self.colors["bg_primary"] if self._tts_enabled else self.colors["text_secondary"],
        )
        status = "🔊 TTS ativado" if self._tts_enabled else "🔇 TTS desativado"
        self._add_system_message(status)

    def _speak_text(self, text: str):
        if not self._tts_enabled or not _HAS_TTS:
            return
        def speak():
            try:
                if self._tts_engine is None:
                    self._tts_engine = pyttsx3.init()
                self._tts_engine.say(text)
                self._tts_engine.runAndWait()
            except Exception as e:
                logger.debug("Falha no TTS: %s", e)
        thread = threading.Thread(target=speak, daemon=True)
        thread.start()

    def _play_notification_sound(self):
        if self._sound_enabled:
            _play_notification()

    def _on_pin_conversation(self, conv_id: int, pinned: bool):
        self.conversation.pin_conversation(conv_id, pinned)
        self.sidebar.refresh(self.conversation.get_conversations(), self.conversation.current_id)

    def _on_search(self, query: str):
        if not query.strip():
            convs = self.conversation.get_conversations()
        else:
            convs = self.conversation.get_conversations(search=query)
        self.sidebar.refresh(convs, self.conversation.current_id)

    def _send_message(self, text: str):
        if self._loading:
            self.chat_display.add_message("⏳  Aguarde a resposta anterior terminar...", "assistant")
            return
        self._loading = True
        self._stop_event.clear()
        self.input_area.set_loading(True)
        self.chat_display.add_message(text, "user")
        self.chat_display.show_typing()

        self._stream_buffer = self.chat_display.start_streaming("assistant")
        self._response_text = ""

        if self._sound_enabled and not self._tts_enabled:
            _play_notification()

        def process():
            try:
                self.conversation.add_message("user", text)
                messages = self.current_agent.get_messages()
                stream_gen = self.ai_manager.send_message(messages, stream=True)
                for chunk in stream_gen:
                    if self._stop_event.is_set():
                        break
                    if chunk:
                        self._response_text += chunk
                        if self._stream_buffer:
                            self._stream_buffer.append(chunk)

                if self._stream_buffer:
                    self._stream_buffer.finalize()
                if self._response_text and not self._stop_event.is_set():
                    self.conversation.add_message("assistant", self._response_text)

                self.after(0, lambda: self.sidebar.refresh(
                    self.conversation.get_conversations(), self.conversation.current_id
                ))
                if self._tts_enabled and self._response_text:
                    self._speak_text(self._response_text)

            except ValueError as e:
                self.after(0, lambda: self._show_error(str(e)))
            except Exception as e:
                logger.error("Erro ao processar mensagem: %s", e)
                self.after(0, lambda e=e: self._show_error(f"Erro: {str(e)}"))
            finally:
                self._loading = False
                self._stream_buffer = None
                self.after(0, lambda: self.input_area.set_loading(False))

        thread = threading.Thread(target=process, daemon=True)
        thread.start()

    def _stop_streaming(self):
        self._stop_event.set()

    def _regenerate_last(self):
        if self._loading or not self.conversation.current_id:
            return
        msgs = self.conversation.get_messages(self.conversation.current_id)
        if not msgs:
            return
        last_user = None
        for m in reversed(msgs):
            if m["role"] == "user":
                last_user = m["content"]
                break
        if not last_user:
            return
        from core.conversation import ConversationManager
        conv_id = self.conversation.current_id
        msg_ids = self.conversation.conn.execute(
            "SELECT id FROM messages WHERE conversation_id = ?", (conv_id,)
        ).fetchall()
        for (mid,) in msg_ids:
            try:
                self.conversation.conn.execute("DELETE FROM messages_fts WHERE rowid = ?", (mid,))
            except Exception:
                pass
        self.conversation.conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
        self.conversation.conn.commit()
        self.chat_display.clear()
        self._send_message(last_user)

    def _show_error(self, msg: str):
        if self._stream_buffer:
            self._stream_buffer.finalize()
        self.chat_display.add_message(f"❌ {msg}", "assistant")

    def _add_system_message(self, text: str):
        self.chat_display.add_message(text, "assistant")

    def _new_conversation(self):
        self.conversation.new_conversation()
        self.chat_display.clear()
        self.sidebar.refresh(self.conversation.get_conversations(), self.conversation.current_id)

    def _load_conversation(self, conv_id: int | None):
        if conv_id is None:
            self._new_conversation()
            return
        self.conversation.current_id = conv_id
        self.chat_display.clear()
        msgs = self.conversation.get_messages(conv_id)
        for msg in msgs:
            self.chat_display.add_message(msg["content"], msg["role"])
        self.sidebar.refresh(self.conversation.get_conversations(), self.conversation.current_id)

    def _delete_conversation(self, conv_id: int):
        if messagebox.askyesno("Confirmar", "Deletar esta conversa?"):
            self.conversation.delete_conversation(conv_id)
            self.chat_display.clear()
            convs = self.conversation.get_conversations()
            if convs:
                self._load_conversation(convs[0]["id"])
            else:
                self._new_conversation()

    def _delete_current_conversation(self):
        if self.conversation.current_id:
            self._delete_conversation(self.conversation.current_id)

    def _clear_chat(self):
        if messagebox.askyesno("Nova conversa", "Limpar a conversa atual e iniciar uma nova?"):
            self._new_conversation()

    def _export_conversation(self):
        if not self.conversation.current_id:
            return
        fmt_map = {
            ("Arquivo de texto (*.txt)", "*.txt"): "txt",
            ("Markdown (*.md)", "*.md"): "md",
            ("PDF (*.pdf)", "*.pdf"): "pdf",
            ("JSON (*.json)", "*.json"): "json",
        }
        filetypes = list(fmt_map.keys())
        path = filedialog.asksaveasfilename(
            title="Exportar conversa",
            filetypes=filetypes,
            defaultextension=".txt",
        )
        if path:
            ext = os.path.splitext(path)[1].lower()
            fmt = "txt"
            for (desc, fext), f in fmt_map.items():
                if fext.replace("*", "") == ext:
                    fmt = f
                    break
            try:
                self.conversation.export_conversation(self.conversation.current_id, path, fmt)
                self._add_system_message(f"📥 Conversa exportada: {os.path.basename(path)}")
            except Exception as e:
                logger.error("Falha ao exportar: %s", e)
                messagebox.showerror("Erro", f"Falha ao exportar: {e}")

    def _minimize_to_tray(self):
        if _HAS_TRAY:
            self._create_tray_icon()

    def _create_tray_icon(self):
        if self._tray_icon:
            return
        try:
            img = Image.new("RGB", (64, 64), (0, 212, 255))
            menu = pystray.Menu(
                pystray.MenuItem("Abrir JARVIS", self._restore_from_tray),
                pystray.MenuItem("Nova Conversa", lambda: self.after(0, self._new_conversation)),
                pystray.MenuItem("Sair", self._quit_from_tray),
            )
            self._tray_icon = pystray.Icon("jarvis", img, "JARVIS AI", menu)
            self.withdraw()
            thread = threading.Thread(target=self._tray_icon.run, daemon=True)
            thread.start()
        except Exception as e:
            logger.error("Falha ao criar icone de bandeja: %s", e)

    def _restore_from_tray(self):
        if self._tray_icon:
            self._tray_icon.stop()
            self._tray_icon = None
        self.deiconify()
        self.lift()
        self.focus_force()

    def _quit_from_tray(self):
        if self._tray_icon:
            self._tray_icon.stop()
            self._tray_icon = None
        self.after(100, self._on_close)

    def _open_settings(self):
        def on_save(data):
            theme = data.get("theme", "")
            if theme:
                self.colors = self.theme_manager.get_colors(theme)
                self.theme_manager.apply_theme(theme, self)
                self._update_theme()

            auto_enabled = data.get("auto_enabled", False)
            tools = data.get("tools", [])
            self.auto_agent.set_auto_mode(auto_enabled, tools)
            self.auto_agent.allowed_tools = tools
            self.auto_switch.select() if auto_enabled else self.auto_switch.deselect()
            self.current_agent = self.auto_agent if auto_enabled else self.chat_agent

            self._sound_enabled = data.get("sound", True)
            auto_theme = data.get("auto_theme", False)
            self.theme_manager.auto_theme = auto_theme
            if auto_theme:
                self._try_auto_theme()

            font_size = data.get("font_size", 13)
            if font_size != self._font_size:
                self._font_size = font_size
                self._update_font_size()

            self._update_provider_label()

        SettingsWindow(self, self.ai_manager, self.theme_manager, self.colors, on_save)

    def _update_font_size(self):
        self.chat_display.rebuild_font()

    def _update_theme(self):
        self.configure(fg_color=self.colors["bg_primary"])
        self.sidebar.update_colors(self.colors)
        self.chat_display.update_colors(self.colors)
        self.input_area.update_colors(self.colors)
        self.logo_label.configure(text_color=self.colors["accent"])

    def _on_close(self):
        logger.info("Encerrando JARVIS")
        self._save_geometry()
        self.conversation.close()
        self.destroy()

    def run(self):
        logger.info("JARVIS iniciado com sucesso")
        self.mainloop()