"""Reusable button component with variants."""
from typing import Callable, Optional

from nicegui import ui


def button(
    label: str,
    on_click: Optional[Callable] = None,
    variant: str = "primary",
    icon: Optional[str] = None,
) -> ui.button:
    btn = ui.button(label, on_click=on_click, icon=icon)
    btn.props("no-caps unelevated")          # normal capitalisation, flat look
    btn.classes("rounded-lg px-6 py-2")
    if variant == "secondary":
        btn.props("outline")
    elif variant == "danger":
        btn.props("color=negative")
    return btn