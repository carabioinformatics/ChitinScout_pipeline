"""Reusable text component with style variants."""
from nicegui import ui

# Tailwind classes for each variant. Change a style here and it
# changes everywhere the variant is used.
TEXT_VARIANTS = {
    "title": "text-3xl font-bold text-slate-800",
    "description": "text-base text-slate-500",
    "body": "text-base text-slate-700",
    "label": "text-xs font-semibold uppercase tracking-wide text-slate-500",
}


def text(content: str, variant: str = "body") -> ui.label:
    if variant not in TEXT_VARIANTS:
        raise ValueError(f"Unknown text variant '{variant}'. Use one of {list(TEXT_VARIANTS)}")
    return ui.label(content).classes(TEXT_VARIANTS[variant])