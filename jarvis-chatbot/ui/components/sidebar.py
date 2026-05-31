import customtkinter as ctk


class _ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self._tip = None
        widget.bind("<Enter>", self._enter, add="+")
        widget.bind("<Leave>", self._leave, add="+")

    def _enter(self, event):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self._tip = ctk.CTkToplevel(self.widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"+{x}+{y}")
        self._tip.configure(fg_color="#333333")
        ctk.CTkLabel(
            self._tip, text=self.text,
            font=ctk.CTkFont(size=11),
            text_color="white",
            padx=8, pady=4,
        ).pack()

    def _leave(self, event):
        if self._tip:
            self._tip.destroy()
            self._tip = None


class SidebarItem(ctk.CTkFrame):
    def __init__(self, master, conv: dict, is_active: bool, colors: dict,
                 on_click, on_delete, on_pin, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.conv_id = conv["id"]
        self.colors = colors
        self.configure(height=48)
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)

        bg = colors["bg_tertiary"] if is_active else "transparent"
        hover = colors["bg_tertiary"]
        border_c = colors["accent"] if is_active else "transparent"

        main_frame = ctk.CTkFrame(self, fg_color=bg, corner_radius=8, height=44)
        main_frame.grid(row=0, column=0, sticky="ew", padx=4, pady=1)
        main_frame.grid_propagate(False)
        main_frame.grid_columnconfigure(0, weight=0)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_columnconfigure(2, weight=0)

        border_indicator = ctk.CTkFrame(
            main_frame, width=3, height=20,
            fg_color=border_c, corner_radius=2,
        )
        border_indicator.grid(row=0, column=0, padx=(4, 4), pady=12)

        pin_text = "📌" if conv.get("pinned") else "💬"
        icon = ctk.CTkLabel(
            main_frame, text=pin_text,
            font=ctk.CTkFont(size=12),
            text_color=colors["accent"] if is_active else colors["text_muted"],
        )
        icon.grid(row=0, column=0, padx=(10 if is_active else 17, 6))

        title = conv["title"][:26] + ("..." if len(conv["title"]) > 26 else "")
        self.title_label = ctk.CTkLabel(
            main_frame, text=title,
            font=ctk.CTkFont(size=12, weight="bold" if is_active else "normal"),
            text_color=colors["text_primary"],
            anchor="w",
        )
        self.title_label.grid(row=0, column=1, sticky="w")
        _ToolTip(self.title_label, conv["title"])

        pin_btn = ctk.CTkButton(
            main_frame, text="📌" if not conv.get("pinned") else "📍",
            width=20, height=20,
            fg_color="transparent",
            hover_color=colors["bg_card"],
            text_color=colors["text_muted"],
            font=ctk.CTkFont(size=10),
            corner_radius=4,
            command=lambda: on_pin(conv["id"], not conv.get("pinned")),
        )
        pin_btn.grid(row=0, column=2, padx=(0, 2))

        del_btn = ctk.CTkButton(
            main_frame, text="✕",
            width=20, height=20,
            fg_color="transparent",
            hover_color=colors["error"],
            text_color=colors["text_muted"],
            font=ctk.CTkFont(size=8),
            corner_radius=4,
            command=lambda: on_delete(conv["id"]),
        )
        del_btn.grid(row=0, column=3, padx=(0, 8))

        main_frame.bind("<Button-1>", lambda e: on_click(conv["id"]))
        main_frame.bind("<Enter>", lambda e: main_frame.configure(
            fg_color=hover if not is_active else colors["bg_tertiary"]
        ))
        main_frame.bind("<Leave>", lambda e: main_frame.configure(
            fg_color=bg
        ))
        for child in main_frame.winfo_children():
            child.bind("<Button-1>", lambda e: on_click(conv["id"]))


class SidebarHeader(ctk.CTkFrame):
    def __init__(self, master, colors: dict, on_new, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent", height=44)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(12, 4))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text="💬 Conversas",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=colors["text_primary"],
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            header, text="＋",
            width=28, height=28,
            fg_color=colors["accent"],
            hover_color=colors["accent_hover"],
            text_color=colors["bg_primary"],
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=8,
            command=on_new,
        ).grid(row=0, column=1)

        search_frame = ctk.CTkFrame(self, fg_color="transparent", height=36)
        search_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(4, 8))
        search_frame.grid_columnconfigure(0, weight=1)

        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text="🔍  Pesquisar...",
            fg_color=colors["bg_tertiary"],
            text_color=colors["text_primary"],
            placeholder_text_color=colors["text_muted"],
            border_width=0,
            corner_radius=8,
            height=32,
            font=ctk.CTkFont(size=12),
        )
        self.search_entry.grid(row=0, column=0, sticky="ew")


class Sidebar(ctk.CTkScrollableFrame):
    def __init__(self, master, colors: dict, conv_callback, delete_callback, **kwargs):
        self.colors = colors
        self.conv_callback = conv_callback
        self.delete_callback = delete_callback
        self.pin_callback = None
        super().__init__(
            master, fg_color=colors["bg_secondary"],
            scrollbar_button_color=colors["border"],
            scrollbar_button_hover_color=colors["text_muted"],
            corner_radius=0,
            **kwargs
        )
        self.configure(width=260)
        self._items: list[SidebarItem] = []
        self._search_callback = None
        self._search_timer = None

        self._build_header()

    def _build_header(self):
        header = SidebarHeader(self, self.colors, on_new=lambda: self.conv_callback(None))
        header.grid(row=0, column=0, sticky="ew")
        header.search_entry.bind("<KeyRelease>", self._on_search_key)
        self._search_entry = header.search_entry
        self._search_var = header.search_var

    def set_pin_callback(self, callback):
        self.pin_callback = callback

    def _on_search_key(self, event):
        if self._search_timer:
            self.after_cancel(self._search_timer)
        self._search_timer = self.after(300, self._do_search)

    def _do_search(self):
        self._search_timer = None
        query = self._search_var.get().strip()
        if self._search_callback:
            self._search_callback(query)

    def set_search_callback(self, callback):
        self._search_callback = callback

    def refresh(self, conversations: list[dict], current_id: int | None = None):
        existing = {}
        for item in self._items:
            existing[item.conv_id] = item

        new_ids = {c["id"] for c in conversations}
        for conv_id, item in list(existing.items()):
            if conv_id not in new_ids:
                item.destroy()
                del existing[conv_id]

        start_row = 1
        if not conversations:
            for item in existing.values():
                item.destroy()
            existing.clear()
            empty_lbl = ctk.CTkLabel(
                self, text="Nenhuma conversa ainda",
                font=ctk.CTkFont(size=12),
                text_color=self.colors["text_muted"],
            )
            empty_lbl.grid(row=start_row, column=0, pady=30)
            self._items = [empty_lbl]
            return

        for conv in conversations:
            conv_id = conv["id"]
            is_active = conv_id == current_id
            if conv_id in existing:
                existing[conv_id].grid(row=start_row, column=0, sticky="ew", pady=1)
            else:
                item = SidebarItem(
                    self, conv, is_active, self.colors,
                    on_click=self.conv_callback,
                    on_delete=self.delete_callback,
                    on_pin=self.pin_callback or (lambda cid, p: None),
                )
                item.grid(row=start_row, column=0, sticky="ew", pady=1)
                existing[conv_id] = item
            start_row += 1

        self._items = list(existing.values())

    def update_colors(self, colors: dict):
        self.colors = colors
        self.configure(fg_color=colors["bg_secondary"],
                       scrollbar_button_color=colors["border"],
                       scrollbar_button_hover_color=colors["text_muted"])