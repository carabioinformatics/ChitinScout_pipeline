from typing import Callable, Optional
from nicegui import ui

def dropdown(
    label: str,
    options: dict,
    value: Optional[str] = None,
    on_change: Optional[Callable] = None,
) -> ui.select:
    """
        Returns: ui.select component with label and list of options specified.
        Value chosen is saved to 'value'. 
    """
    return (
        ui.select(options=options, label=label, value=value, on_change=on_change)
        .props("outlined dense options-dense")
        .classes("w-full")
    )