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
    """
        A slider with its name on the left and its current value on the right.
        Takes text for label, min and max value, the steps taken between, and 
        the descriptive info message that can be displayed alongside.
        format_value turns the raw number into display text, e.g. lambda v: f"{v}%"
        Returns: ui.slider with specified parameters that can retrieve and save value to 'value'.
    """
    format_value = format_value or (lambda v: f"{v:g}")

    with ui.column().classes("w-full gap-0"):
        with ui.row().classes("w-full items-center justify-between"):
            with ui.row().classes("items-center gap-1"):
                text(label, "label")

                # Add info message if possible
                if info_msg:
                    info_button(info_msg, title=label)
            value_label = ui.label()

        # Create slider
        slider = ui.slider(min=minimum, max=maximum, step=step, value=value)
        # Get value
        value_label.bind_text_from(slider, "value", backward=format_value)
    return slider

def info_button(message: str, title: str = "Parameter info") -> ui.button:
    """
        Small 'i' button that opens a standard popup showing `message`.
        Returns: ui.button displaying as an 'i'
    """
    # Create popup box and display message
    with ui.dialog() as dialog, ui.card().classes("w-96 gap-2"):
        text(title, "label")
        text(message, "body")
        # Button to close popup 
        with ui.row().classes("w-full justify-end"):
            ui.button("Close", on_click=dialog.close).props("flat")

    return (
        ui.button(icon="info", on_click=dialog.open)
        .props("flat round dense size=sm color=grey-7")
        .tooltip("More info")
    )
