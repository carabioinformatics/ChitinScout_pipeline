from nicegui import ui

# Variants options with styling
TEXT_VARIANTS = {
    "title": "text-3xl font-bold text-positive",
    "description": "text-base text-slate-900",
    "body": "text-base text-slate-900",
    "label": "text-xs font-semibold uppercase tracking-wide text-primary",
}

def text(content: str, variant: str = "body") -> ui.label:
    """
        This method takes the text specified and applies styling of variant specified.
        Returns: ui.label with specific styling and text.
    """
    if variant not in TEXT_VARIANTS:
        raise ValueError(f"Unknown text variant '{variant}'. Use one of {list(TEXT_VARIANTS)}")
    return ui.label(content).classes(TEXT_VARIANTS[variant])