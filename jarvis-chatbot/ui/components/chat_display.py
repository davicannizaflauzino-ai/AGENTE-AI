import customtkinter as ctk
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import get_formatter_by_name
import re
import time
import webbrowser


def _highlight_code(code: str, lang: str = "") -> str:
    try:
        lexer = get_lexer_by_name(lang) if lang else guess_lexer(code)
        formatter = get_formatter_by_name("html", style="monokai", nowrap=True)
        return highlight(code, lexer, formatter)
    except Exception:
        return code


def _parse_markdown(text: str) -> list[dict]:
    blocks = []
    lines = text.split("\n")
    i = 0
    list_items = []
    in_list = False
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("```thinking"):
            thought_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                thought_lines.append(lines[i])
                i += 1
            i += 1
            if in_list and list_items:
                blocks.append({"type": "list", "items": list_items, "ordered": False})
                list_items = []
                in_list = False
            blocks.append({"type": "thought", "content": "\n".join(thought_lines)})
        elif stripped.startswith("```plan"):
            plan_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                plan_lines.append(lines[i])
                i += 1
            i += 1
            if in_list and list_items:
                blocks.append({"type": "list", "items": list_items, "ordered": False})
                list_items = []
                in_list = False
            blocks.append({"type": "plan", "content": "\n".join(plan_lines)})
        elif line.startswith("```"):
            lang = line[3:].strip()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            if in_list and list_items:
                blocks.append({"type": "list", "items": list_items, "ordered": False})
                list_items = []
                in_list = False
            blocks.append({"type": "code", "lang": lang, "content": "\n".join(code_lines)})
            i += 1
        elif stripped.startswith("|") and stripped.endswith("|") and "---" not in stripped:
            table_rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().split("|")[1:-1]]
                table_rows.append(cells)
                i += 1
            if len(table_rows) >= 2:
                if in_list and list_items:
                    blocks.append({"type": "list", "items": list_items, "ordered": False})
                    list_items = []
                    in_list = False
                blocks.append({"type": "table", "header": table_rows[0], "rows": table_rows[2:]})
            else:
                blocks.append({"type": "text", "content": "\n".join(" | ".join(r) for r in table_rows)})
        elif stripped.startswith("> "):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith("> "):
                quote_lines.append(lines[i].strip()[2:])
                i += 1
            if in_list and list_items:
                blocks.append({"type": "list", "items": list_items, "ordered": False})
                list_items = []
                in_list = False
            blocks.append({"type": "quote", "content": "\n".join(quote_lines)})
        elif stripped.startswith("---") or stripped.startswith("***") or stripped.startswith("___"):
            if in_list and list_items:
                blocks.append({"type": "list", "items": list_items, "ordered": False})
                list_items = []
                in_list = False
            blocks.append({"type": "hr"})
            i += 1
        elif re.match(r'^[\s]*[-*+]\s', stripped):
            in_list = True
            text_content = re.sub(r'^[\s]*[-*+]\s', '', stripped)
            list_items.append({"text": text_content, "level": (len(line) - len(line.lstrip())) // 2})
            i += 1
        elif re.match(r'^[\s]*\d+[.)]\s', stripped):
            in_list = True
            text_content = re.sub(r'^[\s]*\d+[.)]\s', '', stripped)
            list_items.append({"text": text_content, "level": 0, "ordered": True})
            i += 1
        elif stripped == "":
            if in_list and list_items:
                blocks.append({"type": "list", "items": list_items, "ordered": False})
                list_items = []
                in_list = False
            i += 1
        elif line.startswith("### "):
            if in_list and list_items:
                blocks.append({"type": "list", "items": list_items, "ordered": False})
                list_items = []
                in_list = False
            blocks.append({"type": "h3", "content": line[4:]})
            i += 1
        elif line.startswith("## "):
            if in_list and list_items:
                blocks.append({"type": "list", "items": list_items, "ordered": False})
                list_items = []
                in_list = False
            blocks.append({"type": "h2", "content": line[3:]})
            i += 1
        elif line.startswith("# "):
            if in_list and list_items:
                blocks.append({"type": "list", "items": list_items, "ordered": False})
                list_items = []
                in_list = False
            blocks.append({"type": "h1", "content": line[2:]})
            i += 1
        else:
            if in_list:
                blocks.append({"type": "list", "items": list_items, "ordered": False})
                list_items = []
                in_list = False
            content = line
            i += 1
            while i < len(lines) and lines[i].strip() and not lines[i].startswith("```") and not lines[i].startswith("#") and not lines[i].strip().startswith("|") and not lines[i].strip().startswith("> ") and not re.match(r'^[\s]*[-*+]\s', lines[i].strip()) and not re.match(r'^[\s]*\d+[.)]\s', lines[i].strip()):
                content += "\n" + lines[i]
                i += 1
            blocks.append({"type": "text", "content": content})
    if in_list and list_items:
        blocks.append({"type": "list", "items": list_items, "ordered": False})
    return blocks


def _render_inline_markdown(parent, text: str, color: str, colors: dict, wraplength: int = 520):
    parts = re.split(r'(\*\*[^*]+\*\*|`[^`]+`|__[^_]+__|\*[^*]+\*)', text)
    has_formatting = any(p.startswith(("**", "`", "__", "*")) and p.endswith(("**", "`", "__", "*")) for p in parts if p)

    urls = re.findall(r'(https?://[^\s<>"\]\)]+)', text)
    has_urls = bool(urls)

    if not has_formatting and not has_urls:
        lbl = ctk.CTkLabel(
            parent, text=text,
            font=ctk.CTkFont(size=13),
            text_color=color,
            anchor="w", justify="left",
            wraplength=wraplength,
        )
        lbl.pack(side="top", anchor="w", pady=1)
        return

    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(side="top", anchor="w", pady=1)
    for part in parts:
        if part.startswith("**") and part.endswith("**"):
            ctk.CTkLabel(
                frame, text=part[2:-2],
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=color, anchor="w",
            ).pack(side="left")
        elif part.startswith("__") and part.endswith("__"):
            ctk.CTkLabel(
                frame, text=part[2:-2],
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=color, anchor="w",
            ).pack(side="left")
        elif part.startswith("*") and part.endswith("*"):
            ctk.CTkLabel(
                frame, text=part[1:-1],
                font=ctk.CTkFont(size=13, slant="italic"),
                text_color=color, anchor="w",
            ).pack(side="left")
        elif part.startswith("`") and part.endswith("`"):
            ctk.CTkLabel(
                frame, text=part[1:-1],
                font=ctk.CTkFont(size=12, family="Consolas"),
                text_color=colors["accent"],
                fg_color=colors["bg_card"],
                corner_radius=4, padx=5, pady=1,
            ).pack(side="left")
        else:
            remaining = part
            while remaining:
                url_match = re.search(r'(https?://[^\s<>"\]\)]+)', remaining)
                if url_match:
                    before = remaining[:url_match.start()]
                    if before:
                        ctk.CTkLabel(
                            frame, text=before,
                            font=ctk.CTkFont(size=13),
                            text_color=color, anchor="w",
                        ).pack(side="left")
                    url_text = url_match.group(0)
                    url_link = ctk.CTkLabel(
                        frame, text=url_text,
                        font=ctk.CTkFont(size=13, underline=True),
                        text_color=colors["accent"],
                        cursor="hand2",
                    )
                    url_link.pack(side="left")
                    url_link.bind("<Button-1>", lambda e, u=url_text: webbrowser.open(u))
                    remaining = remaining[url_match.end():]
                else:
                    if remaining:
                        ctk.CTkLabel(
                            frame, text=remaining,
                            font=ctk.CTkFont(size=13),
                            text_color=color, anchor="w",
                        ).pack(side="left")
                    remaining = ""


class AvatarCircle(ctk.CTkFrame):
    def __init__(self, master, letter: str, colors: dict, is_user: bool = False, **kwargs):
        size = 36
        super().__init__(master, width=size, height=size, corner_radius=size // 2, **kwargs)
        self.grid_propagate(False)
        bg = colors["user_bubble_accent"] if is_user else colors["ai_bubble_accent"]
        self.configure(fg_color=bg)
        self.label = ctk.CTkLabel(
            self, text=letter,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=colors["bg_primary"],
        )
        self.label.place(relx=0.5, rely=0.5, anchor="center")


class ChatBubble(ctk.CTkFrame):
    def __init__(self, master, message: str, role: str, colors: dict, timestamp: str = "", **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        self.colors = colors
        self.role = role
        self.timestamp = timestamp
        self._blocks: list[ctk.CTkFrame | ctk.CTkLabel] = []
        self._build(message)

    def _build(self, message: str):
        for w in self._blocks:
            w.destroy()
        self._blocks.clear()

        is_user = self.role == "user"
        bubble_bg = self.colors["user_bubble"] if is_user else self.colors["ai_bubble"]
        border_c = self.colors["border_light"] if is_user else self.colors["border"]
        text_color = self.colors["text_primary"]

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        avatar_col = 0 if not is_user else 1
        bubble_col = 1 if not is_user else 0
        avatar_side = "w" if not is_user else "e"
        bubble_side = "w" if not is_user else "e"
        bubble_pad_left = (48, 48) if not is_user else (60, 16)
        bubble_pad_right = (60, 16) if not is_user else (48, 48)

        if is_user:
            bubble_pad_left, bubble_pad_right = bubble_pad_right, bubble_pad_left

        avatar = AvatarCircle(self, "V" if is_user else "J", self.colors, is_user)
        avatar.grid(row=0, column=avatar_col, sticky=avatar_side, padx=(12, 12 if is_user else 0), pady=(12, 0))

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=bubble_col, sticky=bubble_side, padx=bubble_pad_left if not is_user else bubble_pad_right, pady=(8, 0))

        name_color = self.colors["user_bubble_accent"] if is_user else self.colors["ai_bubble_accent"]
        name_label = ctk.CTkLabel(
            header_frame, text="Você" if is_user else "JARVIS",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=name_color,
        )
        name_label.pack(side="left", padx=(0, 6))

        if self.timestamp:
            time_label = ctk.CTkLabel(
                header_frame, text=self.timestamp,
                font=ctk.CTkFont(size=10),
                text_color=self.colors["text_muted"],
            )
            time_label.pack(side="left")

        bubble_frame = ctk.CTkFrame(
            self, fg_color=bubble_bg,
            corner_radius=12,
            border_width=1,
            border_color=border_c,
        )
        bubble_frame.grid(row=1, column=bubble_col, sticky=bubble_side,
                          padx=bubble_pad_left if not is_user else bubble_pad_right,
                          pady=(2, 8))
        bubble_frame.grid_columnconfigure(0, weight=1)
        self.bubble_frame = bubble_frame

        self._render_blocks(bubble_frame, message, text_color)

    def _render_blocks(self, parent, message: str, text_color: str):
        blocks = _parse_markdown(message)
        row = 0
        for block in blocks:
            if block["type"] == "thought":
                self._render_thought(parent, block, row)
                row += 1
            elif block["type"] == "plan":
                self._render_plan(parent, block, row)
                row += 1
            elif block["type"] == "code":
                self._render_code(parent, block, row)
                row += 1
            elif block["type"] in ("h1", "h2", "h3"):
                size = {"h1": 18, "h2": 16, "h3": 15}[block["type"]]
                lbl = ctk.CTkLabel(
                    parent, text=block["content"],
                    font=ctk.CTkFont(size=size, weight="bold"),
                    text_color=self.colors["accent_gradient_start"],
                    anchor="w", justify="left",
                )
                lbl.grid(row=row, column=0, sticky="w", padx=14, pady=(6, 2))
                row += 1
            elif block["type"] == "table":
                self._render_table(parent, block, text_color, row)
                row += 1
            elif block["type"] == "list":
                self._render_list(parent, block, text_color, row)
                row += 1
            elif block["type"] == "quote":
                self._render_quote(parent, block, text_color, row)
                row += 1
            elif block["type"] == "hr":
                self._render_hr(parent, row)
                row += 1
            else:
                self._render_text_block(parent, block["content"], text_color, row)
                row += 1

    def _render_text_block(self, parent, text: str, color: str, row: int):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.grid(row=row, column=0, sticky="ew", padx=14, pady=1)
        container.grid_columnconfigure(0, weight=1)

        text_frame = ctk.CTkFrame(container, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True)
        _render_inline_markdown(text_frame, text, color, self.colors)

        copy_text_btn = ctk.CTkButton(
            container, text="📋", width=20, height=20,
            fg_color="transparent",
            hover_color=self.colors.get("bg_tertiary", "#333"),
            text_color=self.colors["text_muted"],
            font=ctk.CTkFont(size=8),
            corner_radius=4,
            command=lambda t=text: self._copy_text(t),
        )
        copy_text_btn.pack(side="right", anchor="ne", padx=(4, 0))

    def _copy_text(self, text: str):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()

    def _render_quote(self, parent, block: dict, color: str, row: int):
        quote_frame = ctk.CTkFrame(
            parent, fg_color=self.colors["bg_card"],
            corner_radius=6,
        )
        quote_frame.grid(row=row, column=0, sticky="ew", padx=14, pady=2)
        quote_frame.grid_columnconfigure(0, weight=1)

        bar = ctk.CTkFrame(quote_frame, width=3, fg_color=self.colors["accent"], corner_radius=2)
        bar.grid(row=0, column=0, sticky="ns", padx=(4, 4), pady=4)

        label = ctk.CTkLabel(
            quote_frame, text=block["content"],
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_secondary"],
            anchor="w", justify="left", wraplength=480,
        )
        label.grid(row=0, column=1, sticky="w", padx=(0, 8), pady=6)

    def _render_hr(self, parent, row: int):
        hr = ctk.CTkFrame(parent, height=1, fg_color=self.colors["border"])
        hr.grid(row=row, column=0, sticky="ew", padx=14, pady=6)

    def _render_list(self, parent, block: dict, color: str, row: int):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.grid(row=row, column=0, sticky="ew", padx=14, pady=1)
        container.grid_columnconfigure(0, weight=1)
        for idx, item in enumerate(block.get("items", [])):
            prefix = f"{idx+1}. " if item.get("ordered") else "• "
            indent = "  " * item.get("level", 0)
            _render_inline_markdown(container, f"{indent}{prefix}{item['text']}", color, self.colors, wraplength=500)

    def _render_table(self, parent, block: dict, color: str, row: int):
        table_frame = ctk.CTkFrame(parent, fg_color=self.colors["bg_card"], corner_radius=8)
        table_frame.grid(row=row, column=0, sticky="ew", padx=14, pady=4)
        table_frame.grid_columnconfigure(tuple(range(len(block["header"]))), weight=1)

        for col, h in enumerate(block["header"]):
            lbl = ctk.CTkLabel(
                table_frame, text=h,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=self.colors["accent"],
                anchor="w", justify="left",
            )
            lbl.grid(row=0, column=col, sticky="w", padx=6, pady=(4, 2))

        for r_idx, row_data in enumerate(block.get("rows", [])):
            for c_idx, cell in enumerate(row_data):
                lbl = ctk.CTkLabel(
                    table_frame, text=cell,
                    font=ctk.CTkFont(size=11),
                    text_color=color,
                    anchor="w", justify="left",
                )
                lbl.grid(row=r_idx + 1, column=c_idx, sticky="w", padx=6, pady=1)

    def _render_code(self, parent, block: dict, row: int):
        code = block["content"]
        lang = block.get("lang", "")

        code_frame = ctk.CTkFrame(
            parent, fg_color=self.colors["bg_primary"],
            corner_radius=10, border_width=1, border_color=self.colors["border"],
        )
        code_frame.grid(row=row, column=0, sticky="ew", padx=8, pady=4)
        code_frame.grid_columnconfigure(0, weight=1)

        header_bar = ctk.CTkFrame(code_frame, fg_color=self.colors["bg_secondary"], height=32, corner_radius=0)
        header_bar.grid(row=0, column=0, sticky="ew")
        header_bar.grid_propagate(False)
        header_bar.grid_columnconfigure(1, weight=1)

        if lang:
            lang_label = ctk.CTkLabel(
                header_bar, text=f"  {lang}",
                font=ctk.CTkFont(size=11, family="Consolas"),
                text_color=self.colors["text_secondary"],
                anchor="w",
            )
            lang_label.grid(row=0, column=0, sticky="w", padx=10)

        copy_btn = ctk.CTkButton(
            header_bar, text="📋 Copiar",
            width=72, height=22,
            fg_color="transparent",
            hover_color=self.colors["bg_tertiary"],
            text_color=self.colors["text_muted"],
            font=ctk.CTkFont(size=10),
            corner_radius=4,
            command=lambda c=code, b=copy_btn: self._copy_code(c, b),
        )
        copy_btn.grid(row=0, column=2, sticky="e", padx=8)

        code_text = ctk.CTkTextbox(
            code_frame, height=min(300, len(code.split("\n")) * 22 + 20),
            fg_color=self.colors["bg_primary"],
            text_color=self.colors["text_primary"],
            font=ctk.CTkFont(size=12, family="Consolas"),
            border_width=0,
            corner_radius=0,
            wrap="none",
        )
        code_text.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        code_text.insert("1.0", code)
        code_text.configure(state="disabled")

    def _render_thought(self, parent, block: dict, row: int):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.grid(row=row, column=0, sticky="ew", padx=8, pady=2)
        container.grid_columnconfigure(0, weight=1)

        toggle_btn = ctk.CTkButton(
            container, text="🧠  Pensamento  ▼",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=self.colors["bg_card"],
            hover_color=self.colors["bg_tertiary"],
            text_color=self.colors["accent"],
            corner_radius=8, height=28,
            anchor="w",
            command=lambda: self._toggle_section(content_frame, toggle_btn),
        )
        toggle_btn.grid(row=0, column=0, sticky="ew")

        content_frame = ctk.CTkFrame(
            container, fg_color=self.colors["bg_card"],
            corner_radius=8,
        )
        content_frame.grid(row=1, column=0, sticky="ew", pady=(2, 0))
        content_frame.grid_columnconfigure(0, weight=1)

        lbl = ctk.CTkLabel(
            content_frame, text=block["content"],
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color=self.colors["text_secondary"],
            anchor="w", justify="left", wraplength=480,
        )
        lbl.grid(row=0, column=0, sticky="w", padx=10, pady=6)

    def _render_plan(self, parent, block: dict, row: int):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.grid(row=row, column=0, sticky="ew", padx=8, pady=2)
        container.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            container, text="📋  Plano",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["accent"],
        ).grid(row=0, column=0, sticky="w", padx=4, pady=(4, 0))

        lines = block["content"].split("\n")
        for li, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue
            is_step = re.match(r'^[\s]*(\d+[.)]\s)', stripped)
            prefix = "•" if not is_step else ""
            indent = 8 if is_step else 16
            ctk.CTkLabel(
                container, text=f"  {stripped}",
                font=ctk.CTkFont(size=12),
                text_color=self.colors["text_primary"],
                anchor="w", justify="left", wraplength=480,
            ).grid(row=row + 1 + li, column=0, sticky="w", padx=(indent, 4), pady=1)

    def _toggle_section(self, frame, btn):
        if frame.winfo_viewable():
            frame.grid_remove()
            btn.configure(text=btn.cget("text").replace("▼", "▶"))
        else:
            frame.grid()
            btn.configure(text=btn.cget("text").replace("▶", "▼"))

    def _copy_code(self, code: str, btn=None):
        self.clipboard_clear()
        self.clipboard_append(code)
        self.update()
        if btn:
            original = btn.cget("text")
            btn.configure(text="✅ Copiado")
            self.after(1500, lambda: btn.configure(text=original) if btn.winfo_exists() else None)


class TypingIndicator(ctk.CTkFrame):
    def __init__(self, master, colors: dict, **kwargs):
        self.colors = colors
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self._anim_running = True
        self._anim_id = None

        avatar = AvatarCircle(self, "J", colors, False)
        avatar.grid(row=0, column=0, sticky="w", padx=(12, 8), pady=(8, 0))

        dot_frame = ctk.CTkFrame(
            self, fg_color=colors["ai_bubble"],
            corner_radius=12, border_width=1, border_color=colors["border_light"],
        )
        dot_frame.grid(row=0, column=1, sticky="w", padx=(0, 0), pady=(4, 8))
        dot_frame.grid_columnconfigure((0, 1, 2), weight=0)

        self.dots = []
        for i in range(3):
            dot = ctk.CTkLabel(
                dot_frame, text="●",
                font=ctk.CTkFont(size=10),
                text_color=colors["text_muted"],
            )
            dot.grid(row=0, column=i, padx=6, pady=10)
            self.dots.append(dot)

        self._animate_dots(0)

    def destroy(self):
        self._anim_running = False
        if self._anim_id:
            try:
                self.after_cancel(self._anim_id)
            except Exception:
                pass
            self._anim_id = None
        super().destroy()

    def _animate_dots(self, idx):
        if not self._anim_running:
            return
        for i, dot in enumerate(self.dots):
            try:
                dot.configure(text_color=self.colors["accent"] if i == idx else self.colors["text_muted"])
            except Exception:
                self._anim_running = False
                return
        self._anim_id = self.after(400, lambda: self._animate_dots((idx + 1) % 3))


class FindOverlay(ctk.CTkFrame):
    def __init__(self, master, colors, on_close, **kwargs):
        super().__init__(master, fg_color=colors["bg_secondary"], corner_radius=0, height=40, **kwargs)
        self.grid_propagate(False)
        self.grid_columnconfigure(1, weight=1)
        self.colors = colors
        self._on_close = on_close
        self.match_count = 0
        self.current_match = 0
        self._labels: list[tuple[ctk.CTkLabel, int, int, str]] = []

        self.entry = ctk.CTkEntry(
            self, placeholder_text="Buscar no chat...",
            fg_color=colors["bg_tertiary"],
            text_color=colors["text_primary"],
            placeholder_text_color=colors["text_muted"],
            border_color=colors["border"],
            corner_radius=6,
            height=28,
            font=ctk.CTkFont(size=12),
        )
        self.entry.grid(row=0, column=0, padx=(12, 4), pady=6, sticky="w")
        self.entry.bind("<KeyRelease>", self._on_key)
        self.entry.bind("<Return>", lambda e: self._next())

        self.info = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(size=11),
            text_color=colors["text_secondary"],
        )
        self.info.grid(row=0, column=1, sticky="w", padx=4)

        self.up_btn = ctk.CTkButton(
            self, text="▲", width=24, height=24,
            fg_color=colors["bg_tertiary"],
            hover_color=colors["bg_card"],
            text_color=colors["text_primary"],
            font=ctk.CTkFont(size=10),
            corner_radius=4,
            command=self._prev,
        )
        self.up_btn.grid(row=0, column=2, padx=2)

        self.down_btn = ctk.CTkButton(
            self, text="▼", width=24, height=24,
            fg_color=colors["bg_tertiary"],
            hover_color=colors["bg_card"],
            text_color=colors["text_primary"],
            font=ctk.CTkFont(size=10),
            corner_radius=4,
            command=self._next,
        )
        self.down_btn.grid(row=0, column=3, padx=2)

        close_btn = ctk.CTkButton(
            self, text="✕", width=24, height=24,
            fg_color="transparent",
            hover_color=colors["error"],
            text_color=colors["text_muted"],
            font=ctk.CTkFont(size=10),
            corner_radius=4,
            command=self._close,
        )
        close_btn.grid(row=0, column=4, padx=(2, 12))

    def set_labels(self, labels: list):
        self._labels = labels

    def _on_key(self, event):
        query = self.entry.get().strip().lower()
        if not query:
            self.info.configure(text="")
            self._clear_highlights()
            return
        matches = [(lbl, idx, end, txt) for lbl, idx, end, txt in self._labels if query in txt.lower()]
        self.match_count = len(matches)
        self.current_match = 0
        self._clear_highlights()
        if matches:
            self._highlight(matches, 0)

    def _highlight(self, matches, idx):
        self._clear_highlights()
        if not matches:
            return
        lbl, start, end, txt = matches[idx]
        self.current_match = idx
        self.info.configure(text=f"{idx + 1} de {len(matches)}")
        try:
            lbl.configure(text_color=self.colors["accent"])
        except Exception:
            pass
        self._scroll_to(lbl)

    def _clear_highlights(self):
        for lbl, _, _, _ in self._labels:
            try:
                lbl.configure(text_color=self.colors["text_primary"])
            except Exception:
                pass
        self.info.configure(text="")

    def _scroll_to(self, widget):
        try:
            widget.update_idletasks()
            y = widget.winfo_y()
            parent = widget.master
            while parent and parent != self.master:
                y += parent.winfo_y()
                parent = parent.master
            canvas = self.master._parent_canvas_
            if canvas:
                bbox = canvas.bbox("all")
                if bbox and bbox[3] > 0:
                    canvas.yview_moveto(max(0, y / bbox[3]))
        except Exception:
            pass

    def _next(self):
        query = self.entry.get().strip().lower()
        if not query:
            return
        matches = [(lbl, idx, end, txt) for lbl, idx, end, txt in self._labels if query in txt.lower()]
        if not matches:
            return
        idx = (self.current_match + 1) % len(matches)
        self._highlight(matches, idx)

    def _prev(self):
        query = self.entry.get().strip().lower()
        if not query:
            return
        matches = [(lbl, idx, end, txt) for lbl, idx, end, txt in self._labels if query in txt.lower()]
        if not matches:
            return
        idx = (self.current_match - 1) % len(matches)
        self._highlight(matches, idx)

    def _close(self):
        self._clear_highlights()
        self.grid_forget()
        if self._on_close:
            self._on_close()


class ChatDisplay(ctk.CTkScrollableFrame):
    def __init__(self, master, colors: dict, **kwargs):
        self.colors = colors
        self._max_width = 760
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1, minsize=400)
        self._bubbles: list[ChatBubble] = []
        self._typing_indicator: TypingIndicator | None = None
        self._auto_scroll = True
        self._last_role = ""
        self._find_overlay: FindOverlay | None = None

        self.after(100, self._bind_canvas_events)

    def _bind_canvas_events(self):
        try:
            canvas = getattr(self, '_canvas', None)
            if canvas:
                canvas.bind("<Configure>", self._on_canvas_configure, add="+")
        except Exception:
            pass

    @property
    def _parent_canvas_(self):
        return getattr(self, '_canvas', None)

    def show_find(self):
        if not self._find_overlay or not self._find_overlay.winfo_exists():
            self._find_overlay = FindOverlay(self, self.colors, on_close=self._on_find_close)
        self._find_overlay.grid(row=0, column=0, sticky="ew")
        self._find_overlay.entry.focus_set()
        labels = []
        for b in self._bubbles:
            for child in b.winfo_children():
                self._collect_labels(child, labels)
        self._find_overlay.set_labels(labels)

    def _on_find_close(self):
        self._find_overlay = None
        self.focus_set()

    def _collect_labels(self, widget, labels: list):
        if isinstance(widget, ctk.CTkLabel):
            txt = widget.cget("text")
            if txt:
                start = widget.grid_info().get("row", 0)
                labels.append((widget, start, 0, txt))
        for child in widget.winfo_children():
            self._collect_labels(child, labels)

    def hide_find(self):
        if self._find_overlay:
            self._find_overlay._close()

    def _on_canvas_configure(self, event):
        self._update_max_width()

    def _update_max_width(self):
        try:
            w = self._canvas.winfo_width() - 30
            self._max_width = max(400, w)
        except Exception:
            pass

    def set_auto_scroll(self, enabled: bool):
        self._auto_scroll = enabled
        if enabled:
            self._scroll_to_bottom()

    def toggle_auto_scroll(self):
        self.set_auto_scroll(not self._auto_scroll)
        return self._auto_scroll

    def add_message(self, message: str, role: str):
        self._hide_typing()
        ts = time.strftime("%d/%m %H:%M")
        bubble = ChatBubble(self, message, role, self.colors, timestamp=ts)
        bubble.grid(row=len(self._bubbles) * 2, column=0, sticky="ew", pady=1)
        self._bubbles.append(bubble)
        self._last_role = role
        self._scroll_to_bottom()

    def show_typing(self):
        self._hide_typing()
        self._typing_indicator = TypingIndicator(self, self.colors)
        self._typing_indicator.grid(
            row=len(self._bubbles) * 2 + 1, column=0, sticky="w", pady=1
        )
        self._scroll_to_bottom()

    def _hide_typing(self):
        if self._typing_indicator:
            self._typing_indicator.destroy()
            self._typing_indicator = None

    def start_streaming(self, role: str = "assistant"):
        self._hide_typing()
        ts = time.strftime("%d/%m %H:%M")
        bubble = ChatBubble(self, "", role, self.colors, timestamp=ts)
        bubble.grid(row=len(self._bubbles) * 2, column=0, sticky="ew", pady=1)
        self._bubbles.append(bubble)
        self._scroll_to_bottom()
        return StreamingBuffer(bubble)

    def clear(self):
        for b in self._bubbles:
            b.destroy()
        self._bubbles.clear()
        self._hide_typing()
        self._last_role = ""

    def update_colors(self, colors: dict):
        self.colors = colors
        for b in self._bubbles:
            b.colors = colors

    def rebuild_font(self):
        for b in self._bubbles:
            first = next((w for w in b._blocks if isinstance(w, ctk.CTkLabel) or True), None)
            b._build(b._blocks[0].cget("text") if b._blocks else "")

    def _scroll_to_bottom(self):
        if not self._auto_scroll:
            return

        def scroll():
            try:
                self._canvas.yview_moveto(1.0)
            except Exception:
                pass
        self.after(30, scroll)


class StreamingBuffer:
    def __init__(self, bubble: ChatBubble):
        self.bubble = bubble
        self._buffer = ""
        self._pending = ""
        self._update_id = None
        self._last_update = 0.0

    def append(self, chunk: str):
        self._pending += chunk
        if self._update_id is None:
            self._flush()

    def _flush(self):
        if not self._pending:
            self._update_id = None
            return
        self._buffer += self._pending
        self._pending = ""
        root = self.bubble.winfo_toplevel()
        if root:
            self.bubble._build(self._buffer)
            now = time.time()
            delay = 16 if (now - self._last_update) < 0.1 else 8
            self._last_update = now
            self._update_id = root.after(int(delay), self._flush)

    def finalize(self):
        if self._update_id:
            root = self.bubble.winfo_toplevel()
            if root:
                root.after_cancel(self._update_id)
            self._update_id = None
        self._buffer += self._pending
        self._pending = ""
        self.bubble._build(self._buffer)

    def get_text(self) -> str:
        return self._buffer