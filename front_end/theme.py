from nicegui import ui

# Colours
PRIMARY = "#0f766e"    # teal
SECONDARY = "#6366f1"  # indigo
ACCENT = "#f59e0b"     # amber
POSITIVE = "#16a34a"   # green
NEGATIVE = "#dc2626"   # red
INFO = "#0284c7"       # blue

def apply_theme() -> None:
    """
        This method sets the global styling for this User interface. 
        Can be called at the top of each page and will then apply theme.
    """
    ui.colors(
        primary=PRIMARY,
        secondary=SECONDARY,
        accent=ACCENT,
        positive=POSITIVE,
        negative=NEGATIVE,
        info=INFO,
    )
    ui.query("body").classes("bg-slate-100")