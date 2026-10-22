"""One place for colours and global styling."""
from nicegui import ui

PRIMARY = "#0f766e"    # teal
SECONDARY = "#6366f1"  # indigo
ACCENT = "#f59e0b"     # amber
POSITIVE = "#16a34a"   # green
NEGATIVE = "#dc2626"   # red
INFO = "#0284c7"       # blue


def apply_theme() -> None:
    """Call once at the top of every page."""
    ui.colors(
        primary=PRIMARY,
        secondary=SECONDARY,
        accent=ACCENT,
        positive=POSITIVE,
        negative=NEGATIVE,
        info=INFO,
    )
    ui.query("body").classes("bg-slate-100")