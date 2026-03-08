"""Shared chart tooltip helpers for visualization and UI layers.

This module provides a UI-independent home for hoverlabel and hover template
helpers so visualization modules do not depend on the ui/ layer.
"""

from __future__ import annotations

# Keep values aligned with ui.style_constants tooltip defaults.
TOOLTIP_STYLES: dict[str, dict[str, str | int]] = {
    "default": {
        "bgcolor": "rgba(33, 37, 41, 0.95)",
        "bordercolor": "rgba(255, 255, 255, 0.1)",
        "fontcolor": "#f8f9fa",
        "fontsize": 14,
    },
    "dark": {
        "bgcolor": "rgba(33, 37, 41, 0.95)",
        "bordercolor": "rgba(255, 255, 255, 0.1)",
        "fontcolor": "#f8f9fa",
        "fontsize": 14,
    },
    "success": {
        "bgcolor": "rgba(240, 255, 240, 0.95)",
        "bordercolor": "rgb(40, 167, 69)",
        "fontcolor": "#343a40",
        "fontsize": 14,
    },
    "warning": {
        "bgcolor": "rgba(255, 252, 235, 0.95)",
        "bordercolor": "rgb(255, 193, 7)",
        "fontcolor": "#343a40",
        "fontsize": 14,
    },
    "error": {
        "bgcolor": "rgba(255, 235, 235, 0.95)",
        "bordercolor": "rgb(220, 53, 69)",
        "fontcolor": "#343a40",
        "fontsize": 14,
    },
    "info": {
        "bgcolor": "rgba(235, 250, 255, 0.95)",
        "bordercolor": "rgb(13, 202, 240)",
        "fontcolor": "#343a40",
        "fontsize": 14,
    },
    "primary": {
        "bgcolor": "rgba(235, 245, 255, 0.95)",
        "bordercolor": "rgb(13, 110, 253)",
        "fontcolor": "#343a40",
        "fontsize": 14,
    },
}

_FONT_FAMILY = "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"


def _get_tooltip_style(variant: str = "default") -> dict[str, str | int]:
    if variant in TOOLTIP_STYLES:
        return TOOLTIP_STYLES[variant]
    return TOOLTIP_STYLES["default"]


def create_hoverlabel_config(variant: str = "default") -> dict:
    style = _get_tooltip_style(variant)
    return {
        "bgcolor": style["bgcolor"],
        "bordercolor": style["bordercolor"],
        "font": {
            "family": _FONT_FAMILY,
            "size": style["fontsize"],
            "color": style["fontcolor"],
        },
    }


def format_hover_template(
    title: str | None = None,
    fields: dict | None = None,
    extra_info: str | None = None,
    include_extra_tag: bool = True,
) -> str:
    template: list[str] = []

    if title:
        template.append(f"<b>{title}</b><br>")

    if fields:
        for label, value in fields.items():
            template.append(f"{label}: {value}<br>")

    hover_text = "".join(template)

    if include_extra_tag:
        if extra_info:
            return f"{hover_text}<extra>{extra_info}</extra>"
        return f"{hover_text}<extra></extra>"

    return hover_text
