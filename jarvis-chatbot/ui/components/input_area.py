import customtkinter as ctk
import threading

try:
    import speech_recognition as sr
    _HAS_SPEECH = True
except ImportError:
    _HAS_SPEECH = False


class InputArea(ctk.CTkFrame):
    def __init__(self, master, colors: dict, send_callback, stop_callback=None, **kwargs):
        self.colors = colors
        self.send_callback = send_callback
        self.stop_callback = stop_callback
        self._min_height = 52
        self._max_height = 160
        self._listening = False
        self._loading = False
        super().__init__(master, fg_color="transparent", **kwargs)
        self.configure(height=self._min_height)
        self.grid_columnconfigure(0, weight=1)
        self.grid_propagate(False)

        container = ctk.CTkFrame(
            self,
            fg_color=colors["bg_secondary"],
            corner_radius=16,
            border_width=1,
            border_color=colors["border"],
        )
        container.grid(row=0, column=0, sticky="nsew", padx=0, pady=(0, 0))
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        self.textbox = ctk.CTkTextbox(
            container,
            height=self._min_height - 8,
            fg_color="transparent",
            text_color=colors["text_primary"],
            border_width=0,
            corner_radius=0,
            font=ctk.CTkFont(size=13),
            wrap="word",
            padx=16,
            pady=10,
        )
        self.textbox.grid(row=0, column=0, sticky="nsew", padx=(0, 0))
        self.textbox.insert("1.0", "Digite sua mensagem...")
        self.placeholder_active = True
        self.textbox.bind("<FocusIn>", self._on_focus_in)
        self.textbox.bind("<FocusOut>", self._on_focus_out)
        self.textbox.bind("<KeyRelease>", self._on_key_release)

        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.grid(row=0, column=1, sticky="s", padx=(0, 6), pady=6)

        self.mic_btn = ctk.CTkButton(
            btn_frame,
            text="🎤",
            width=34,
            height=34,
            fg_color=colors["bg_tertiary"],
            hover_color=colors["bg_card"],
            text_color=colors["text_muted"],
            font=ctk.CTkFont(size=14),
            corner_radius=10,
            command=self._toggle_mic,
        )
        self.mic_btn.pack(side="top", pady=(0, 2))

        self.send_btn = ctk.CTkButton(
            btn_frame,
            text="➤",
            width=34,
            height=34,
            fg_color=colors["accent"],
            hover_color=colors["accent_hover"],
            text_color=colors["bg_primary"],
            font=ctk.CTkFont(size=16),
            corner_radius=10,
            command=self._send_or_stop,
        )
        self.send_btn.pack(side="top")

        self.textbox.bind("<Return>", self._on_enter)
        self.textbox.bind("<Shift-Return>", self._on_shift_enter)

    def _on_focus_in(self, event):
        if self.placeholder_active:
            self.textbox.delete("1.0", "end-1c")
            self.placeholder_active = False

    def _on_focus_out(self, event):
        if not self.textbox.get("1.0", "end-1c").strip():
            self.textbox.insert("1.0", "Digite sua mensagem...")
            self.placeholder_active = True

    def _on_enter(self, event):
        self._send()
        return "break"

    def _on_shift_enter(self, event):
        return None

    def _on_key_release(self, event):
        self._auto_resize()

    def _auto_resize(self):
        if self.placeholder_active:
            return
        try:
            line_count = int(self.textbox.index("end-1c").split(".")[0])
            visible_lines = max(line_count, 1)
            new_height = min(visible_lines * 24 + 16, self._max_height)
            new_height = max(new_height, self._min_height)
            self.textbox.configure(height=new_height - 8)
            self.configure(height=new_height)
        except Exception:
            pass

    def _send(self):
        text = self.textbox.get("1.0", "end-1c").strip()
        if text and text != "Digite sua mensagem...":
            self.textbox.delete("1.0", "end-1c")
            self.placeholder_active = False
            self._auto_resize()
            self.send_callback(text)

    def _send_or_stop(self):
        if self._loading:
            if self.stop_callback:
                self.stop_callback()
        else:
            self._send()

    def _toggle_mic(self):
        if not _HAS_SPEECH:
            self._insert_text("[🎤 speech_recognition não instalado]")
            return
        if self._listening:
            return
        self._listening = True
        self.mic_btn.configure(fg_color=self.colors["error"], text="🔴")
        def listen():
            try:
                r = sr.Recognizer()
                with sr.Microphone() as source:
                    r.adjust_for_ambient_noise(source, duration=0.5)
                    audio = r.listen(source, timeout=5, phrase_time_limit=10)
                text = r.recognize_google(audio, language="pt-BR")
                self.after(0, lambda: self._insert_text(text))
            except sr.WaitTimeoutError:
                self.after(0, lambda: self._insert_text(""))
            except sr.UnknownValueError:
                self.after(0, lambda: self._insert_text(""))
            except Exception as e:
                self.after(0, lambda: self._insert_text(f"[Erro: {e}]"))
            finally:
                self._listening = False
                self.after(0, lambda: self.mic_btn.configure(
                    fg_color=self.colors["bg_tertiary"], text="🎤"
                ))
        thread = threading.Thread(target=listen, daemon=True)
        thread.start()

    def _insert_text(self, text: str):
        if self.placeholder_active:
            self.textbox.delete("1.0", "end-1c")
            self.placeholder_active = False
        self.textbox.insert("end", text)
        self._auto_resize()

    def update_colors(self, colors: dict):
        self.colors = colors
        self.textbox.configure(text_color=colors["text_primary"])
        self.send_btn.configure(
            fg_color=colors["accent"],
            hover_color=colors["accent_hover"],
            text_color=colors["bg_primary"],
        )

    def set_loading(self, loading: bool):
        self._loading = loading
        if loading:
            self.send_btn.configure(text="⏹", fg_color=self.colors.get("error", "#e74c3c"))
        else:
            self.send_btn.configure(text="➤", fg_color=self.colors["accent"])