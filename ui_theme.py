import tkinter as tk


COLORS = {
    "app_bg": "#F4F7FB",
    "panel_bg": "#FFFFFF",
    "panel_border": "#D8E0EA",
    "text": "#1F2937",
    "muted": "#64748B",
    "primary": "#2563EB",
    "primary_hover": "#1D4ED8",
    "secondary": "#0F766E",
    "secondary_hover": "#115E59",
    "warning": "#B45309",
    "warning_hover": "#92400E",
    "danger": "#DC2626",
    "danger_hover": "#B91C1C",
}


def configure_root(root, bg=None):
    """Apply shared defaults for a cleaner Tkinter look."""
    root.configure(bg=bg or COLORS["app_bg"])
    root.option_add("*Font", ("Segoe UI", 11))
    root.option_add("*Foreground", COLORS["text"])
    root.option_add("*Background", bg or COLORS["app_bg"])
    root.option_add("*Entry.Background", COLORS["panel_bg"])
    root.option_add("*Entry.Relief", "flat")
    root.option_add("*Entry.HighlightThickness", 1)
    root.option_add("*Entry.HighlightBackground", COLORS["panel_border"])


def button(parent, text, command, variant="primary", **kwargs):
    """Create a modern flat button with hover colors."""
    bg = COLORS[variant]
    hover = COLORS[f"{variant}_hover"]
    btn = tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg,
        fg="white",
        activebackground=hover,
        activeforeground="white",
        relief="flat",
        bd=0,
        padx=14,
        pady=8,
        cursor="hand2",
        **kwargs
    )

    def on_enter(_event):
        if btn.cget("state") != "disabled":
            btn.configure(bg=hover)

    def on_leave(_event):
        if btn.cget("state") != "disabled":
            btn.configure(bg=bg)

    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    return btn


def panel(parent, **kwargs):
    """Create a white panel with a subtle border."""
    return tk.Frame(
        parent,
        bg=COLORS["panel_bg"],
        highlightbackground=COLORS["panel_border"],
        highlightthickness=1,
        bd=0,
        **kwargs
    )
