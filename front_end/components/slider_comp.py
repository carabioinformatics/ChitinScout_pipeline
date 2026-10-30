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
    info_msg: str,
    format_value: Optional[Callable[[float], str]] = None,
) -> ui.slider:
    """A slider with its name on the left and its current value on the right.

    format_value turns the raw number into display text,
    e.g. lambda v: f"{v}%"
    """
    format_value = format_value or (lambda v: f"{v:g}")

    with ui.column().classes("w-full gap-0"):
        with ui.row().classes("w-full items-center justify-between"):
            with ui.row().classes("items-center gap-1"):
                ui.label(label)
                if info_msg:
                    info_button(info_msg, title=label)   # <-- the new part
            value_label = ui.label()

        slider = ui.slider(min=minimum, max=maximum, step=step, value=value)
        value_label.bind_text_from(slider, "value", backward=format_value)
    return slider

def info_button(message: str, title: str = "Parameter info") -> ui.button:
    """Small 'i' button that opens a standard popup showing `message`."""
    with ui.dialog() as dialog, ui.card().classes("w-96 gap-2"):
        ui.label(title).classes("text-lg font-semibold")
        ui.label(message).classes("text-sm text-gray-700 whitespace-pre-line")
        with ui.row().classes("w-full justify-end"):
            ui.button("Close", on_click=dialog.close).props("flat")

    return (
        ui.button(icon="info", on_click=dialog.open)
        .props("flat round dense size=sm color=grey-7")
        .tooltip("More info")
    )
