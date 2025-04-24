"""
Icon Utilities Module

This module provides standardized icon functionality and semantic naming
for consistent icon usage across the application.
"""

#######################################################################
# IMPORTS
#######################################################################
# Third-party library imports
import dash_bootstrap_components as dbc
from dash import html

#######################################################################
# ICON MAPPING
#######################################################################
# Mapping of semantic names to Font Awesome icon classes
ICON_MAP = {
    # Action icons
    "add": "fa-plus",
    "delete": "fa-trash",
    "edit": "fa-edit",
    "save": "fa-save",
    "upload": "fa-upload",
    "download": "fa-download",
    "export": "fa-file-export",
    "import": "fa-file-import",
    "refresh": "fa-sync",
    "filter": "fa-filter",
    "search": "fa-search",
    "close": "fa-times",
    "cancel": "fa-ban",
    "settings": "fa-cog",
    # Status/indicator icons
    "success": "fa-check-circle",
    "error": "fa-exclamation-circle",
    "warning": "fa-exclamation-triangle",
    "info": "fa-info-circle",
    "help": "fa-question-circle",
    # Data visualization icons
    "chart": "fa-chart-bar",
    "trend_up": "fa-chart-line",
    "trend_down": "fa-chart-line fa-flip-vertical",
    "points": "fa-chart-bar",
    "items": "fa-tasks",
    "forecast": "fa-chart-line",
    "burndown": "fa-chart-area",
    "deadline": "fa-calendar-day",
    # Navigation icons
    "next": "fa-chevron-right",
    "previous": "fa-chevron-left",
    "expand": "fa-chevron-down",
    "collapse": "fa-chevron-up",
    "home": "fa-home",
    # Project management icons
    "calendar": "fa-calendar-alt",
    "time": "fa-clock",
    "user": "fa-user",
    "team": "fa-users",
    "task": "fa-clipboard-check",
    "story": "fa-sticky-note",
    "epic": "fa-bookmark",
    # Misc icons
    "document": "fa-file-alt",
    "code": "fa-code",
    "github": "fa-github",
}

#######################################################################
# ICON SIZE MAP
#######################################################################
# Standard sizes for icons based on context
ICON_SIZES = {
    "xs": "0.75em",
    "sm": "0.875em",
    "md": "1em",
    "lg": "1.25em",
    "xl": "1.5em",
    "xxl": "2em",
}

#######################################################################
# FUNCTIONS
#######################################################################


def get_icon_class(icon_name, solid=True):
    """
    Get the full Font Awesome class for an icon by its semantic name.

    Args:
        icon_name (str): Semantic name of the icon
        solid (bool): Whether to use solid or regular style (default: solid)

    Returns:
        str: Full Font Awesome class including fa-prefix
    """
    icon_style = "fas" if solid else "far"  # Use solid by default

    # If the semantic name exists in our map, use it
    if icon_name in ICON_MAP:
        icon_class = ICON_MAP[icon_name]
    else:
        # Otherwise, assume it's already a Font Awesome class without the prefix
        icon_class = icon_name

    return f"{icon_style} {icon_class}"


def create_icon(icon_name, size="md", color=None, className="", solid=True, style=None):
    """
    Create an icon element with standardized styling.

    Args:
        icon_name (str): Semantic name of the icon or Font Awesome class
        size (str): One of xs, sm, md, lg, xl, xxl
        color (str): CSS color value
        className (str): Additional CSS classes
        solid (bool): Whether to use solid or regular style
        style (dict): Additional inline styles

    Returns:
        html.I: Icon component
    """
    icon_class = get_icon_class(icon_name, solid)

    # Build style dict
    icon_style = style or {}
    if size in ICON_SIZES:
        icon_style["fontSize"] = ICON_SIZES[size]
    if color:
        icon_style["color"] = color

    # Combine classes
    classes = f"{icon_class} {className}".strip()

    return html.I(className=classes, style=icon_style)


def create_icon_text(
    icon_name,
    text,
    size="md",
    color=None,
    spacing="0.5rem",
    className="",
    reverse=False,
    solid=True,
    style=None,
):
    """
    Create an icon with text, ensuring proper alignment and spacing.

    Args:
        icon_name (str): Semantic name of the icon or Font Awesome class
        text (str or component): Text or component to display next to the icon
        size (str): Icon size (xs, sm, md, lg, xl, xxl)
        color (str): Color for both icon and text
        spacing (str): Space between icon and text
        className (str): Additional CSS classes for the container
        reverse (bool): If True, show text before icon
        solid (bool): Whether to use solid or regular icon style
        style (dict): Additional inline styles for container

    Returns:
        html.Div: Container with icon and text properly aligned
    """
    container_style = {"display": "inline-flex", "alignItems": "center", "gap": spacing}

    # Add any custom styles
    if style:
        container_style.update(style)

    # Create icon with consistent alignment
    icon = create_icon(
        icon_name,
        size=size,
        color=color,
        solid=solid,
        style={"display": "inline-flex", "alignItems": "center"},
    )

    # Create text element if it's a string
    text_el = html.Span(text, style={"color": color} if color else {})

    # Order the elements based on reverse flag
    children = [text_el, icon] if reverse else [icon, text_el]

    return html.Div(children, className=className, style=container_style)
