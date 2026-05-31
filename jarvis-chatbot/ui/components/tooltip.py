import customtkinter as ctk


class ToolTip:
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
