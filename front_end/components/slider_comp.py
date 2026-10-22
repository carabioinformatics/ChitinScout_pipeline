"""Reusable slider component with a label and live value display."""
from typing import Callable, Optional
from nicegui import ui
from front_end.components.text_comp import text


def labeled_slider(
    label: str,
    minimum: float,
    maximum: float,
    step: float,
    value: float,
    format_value: Optional[Callable[[float], str]] = None,
) -> ui.slider:
    """A slider with its name on the left and its current value on the right.

    format_value turns the raw number into display text,
    e.g. lambda v: f"{v}%"
    """
    format_value = format_value or (lambda v: f"{v:g}")

    with ui.column().classes("w-full gap-0"):
        with ui.row().classes("w-full justify-between items-center"):
            text(label, "body")
            value_label = text("", "body").classes("font-semibold")
        slider = ui.slider(min=minimum, max=maximum, step=step, value=value).props("snap")
        value_label.bind_text_from(slider, "value", backward=format_value)

    return slider