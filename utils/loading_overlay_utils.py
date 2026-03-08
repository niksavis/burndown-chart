"""Shared loading overlay helpers for non-UI layers."""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import html

_SPINNER_COLORS: dict[str, str] = {
    "primary": "rgb(13, 110, 253)",
    "secondary": "rgb(108, 117, 125)",
    "success": "rgb(40, 167, 69)",
    "warning": "rgb(255, 193, 7)",
    "danger": "rgb(220, 53, 69)",
    "info": "rgb(13, 202, 240)",
}


def _create_spinner(
    style_key: str = "primary",
    size_key: str = "md",
    text: str | None = None,
):
    color = _SPINNER_COLORS.get(style_key, _SPINNER_COLORS["primary"])
    size = "sm" if size_key in {"xs", "sm"} else "md"

    spinner = dbc.Spinner(type="border", color=color, size=size)

    if not text:
        return spinner

    return html.Div(
        [spinner, html.Div(text, className="text-center mt-2 text-muted small")],
        className="d-flex flex-column align-items-center justify-content-center py-3",
    )


def create_loading_overlay(
    children,
    style_key: str = "primary",
    size_key: str = "md",
    text: str | None = None,
    is_loading: bool = False,
    opacity: float = 0.7,
    className: str = "",
):
    """Create a loading overlay component wrapping arbitrary children."""
    if not is_loading:
        return html.Div(children, className=className)

    overlay_style = {
        "position": "absolute",
        "top": "0",
        "left": "0",
        "width": "100%",
        "height": "100%",
        "backgroundColor": f"rgba(248, 249, 250, {opacity})",
        "display": "flex",
        "justifyContent": "center",
        "alignItems": "center",
        "zIndex": "1000",
    }

    spinner = _create_spinner(style_key, size_key, text)

    return html.Div(
        [
            html.Div(spinner, style=overlay_style),
            html.Div(children, style={"filter": "blur(1px)"}),
        ],
        style={"position": "relative"},
        className=className,
    )
