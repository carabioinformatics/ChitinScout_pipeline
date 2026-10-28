"""Reusable text component with style variants."""
from nicegui import ui

# Tailwind classes for each variant. Change a style here and it
# changes everywhere the variant is used.
TEXT_VARIANTS = {
    "title": "text-3xl font-bold text-positive",
    "description": "text-base text-slate-900",
    "body": "text-base text-slate-900",
    "label": "text-xs font-semibold uppercase tracking-wide text-primary",
}


def text(content: str, variant: str = "body") -> ui.label:
    if variant not in TEXT_VARIANTS:
        raise ValueError(f"Unknown text variant '{variant}'. Use one of {list(TEXT_VARIANTS)}")
    return ui.label(content).classes(TEXT_VARIANTS[variant])