from typing import Callable, Optional
from nicegui import ui

def button(
    label: str,
    on_click: Optional[Callable] = None,
    variant: str = "primary",
    icon: Optional[str] = None,
) -> ui.button:
    """
        This is a reusable component with predefined variants. Can specifify the label and (optional) icon 
        displayed on the button, as well as the action that should be taken when clicked.
        Returns: ui.button with specified label, additional icon, and what should happen when clicked.
    """
    btn = ui.button(label, on_click=on_click, icon=icon)
    btn.props("no-caps unelevated")
    btn.classes("rounded-lg px-6 py-2")
    
    if variant == "secondary":
        btn.props("outline")
    elif variant == "danger":
        btn.props("color=negative")
    return btn