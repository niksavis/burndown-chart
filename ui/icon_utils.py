"""
Icon Utilities Module

This module provides a standardized icon system for the application.
It contains functions for creating and styling icons with consistent appearance.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
# (none currently needed)

# Third-party library imports
from dash import html

# Application imports
from ui.styles import get_color, SPACING

#######################################################################
# CONSTANTS
#######################################################################

# Icon size constants
ICON_SIZES = {
    "xs": "0.75rem",  # 12px
    "sm": "0.875rem",  # 14px
    "md": "1rem",  # 16px
    "lg": "1.25rem",  # 20px
    "xl": "1.5rem",  # 24px
    "xxl": "2rem",  # 32px
}

# Semantic icon mappings
SEMANTIC_ICONS = {
    # Data & Charts
    "items": "fas fa-tasks",
    "points": "fas fa-chart-line",
    "statistics": "fas fa-table",
    "chart": "fas fa-chart-bar",
    "data": "fas fa-database",
    "calendar": "fas fa-calendar-day",
    "date": "fas fa-calendar-alt",
    "deadline": "fas fa-calendar-times",
    # Status indicators
    "success": "fas fa-check-circle",
    "warning": "fas fa-exclamation-triangle",
    "danger": "fas fa-exclamation-circle",
    "info": "fas fa-info-circle",
    # Trends
    "trend_up": "fas fa-arrow-up",
    "trend_down": "fas fa-arrow-down",
    "trend_neutral": "fas fa-equals",
    # Actions
    "add": "fas fa-plus",
    "edit": "fas fa-pencil-alt",
    "delete": "fas fa-trash",
    "save": "fas fa-save",
    "download": "fas fa-download",
    "upload": "fas fa-upload",
    "export": "fas fa-file-export",
    "import": "fas fa-file-import",
    # Navigation
    "back": "fas fa-arrow-left",
    "forward": "fas fa-arrow-right",
    "home": "fas fa-home",
    "settings": "fas fa-cog",
    "help": "fas fa-question-circle",
}

# Default icon styling
DEFAULT_ICON_STYLES = {
    "marginRight": SPACING["sm"],  # Default right margin for icon+text pattern
    "display": "inline-block",  # Ensure proper alignment with text
    "verticalAlign": "middle",  # Default vertical alignment
    "lineHeight": "1",  # Prevent height discrepancies
}

#######################################################################
# ICON UTILITY FUNCTIONS
#######################################################################


def get_icon_class(icon_key):
    """
    Get Font Awesome icon class from semantic icon key.

    Args:
        icon_key (str): Semantic icon name (e.g. 'success', 'items')

    Returns:
        str: Font Awesome icon class
    """
    return SEMANTIC_ICONS.get(icon_key, icon_key)


def create_icon(
    icon,
    color=None,
    size="md",
    className="",
    style=None,
    with_fixed_width=True,
    with_space_right=False,
    with_space_left=False,
    id=None,
):
    """
    Create a standardized icon component with consistent styling.

    Args:
        icon (str): Icon key from SEMANTIC_ICONS or direct Font Awesome class
        color (str, optional): Color key or CSS color value
        size (str, optional): Size key from ICON_SIZES or CSS size
        className (str, optional): Additional CSS classes
        style (dict, optional): Additional inline styles
        with_fixed_width (bool): Apply the 'fa-fw' class for fixed width icons
        with_space_right (bool): Add space to the right of the icon
        with_space_left (bool): Add space to the left of the icon
        id (str, optional): Component ID

    Returns:
        html.I: Icon component with standardized styling
    """
    icon_class = get_icon_class(icon)

    # Apply fixed width class if needed
    if with_fixed_width and "fa-fw" not in icon_class:
        icon_class = f"{icon_class} fa-fw"

    # Apply spacing classes
    if with_space_right:
        className = f"{className} me-2"
    if with_space_left:
        className = f"{className} ms-2"

    # Ensure icon has proper base class (font awesome)
    if not any(
        prefix in icon_class for prefix in ["fas ", "far ", "fab ", "fal ", "fad "]
    ):
        icon_class = f"fas {icon_class}"

    # Build icon style
    icon_style = dict(DEFAULT_ICON_STYLES)

    # Add color if provided
    if color:
        icon_style["color"] = get_color(color)

    # Add size if provided
    if size in ICON_SIZES:
        icon_style["fontSize"] = ICON_SIZES[size]
    elif size:  # direct CSS value
        icon_style["fontSize"] = size

    # Add custom styles
    if style:
        icon_style.update(style)

    return html.I(
        className=icon_class + (f" {className}" if className else ""),
        style=icon_style,
        id=id,
    )


def create_icon_text(
    icon,
    text,
    color=None,
    icon_color=None,
    size="md",
    icon_size=None,
    icon_position="left",
    className="",
    text_style=None,
    alignment="center",
    id=None,
):
    """
    Create a standardized icon + text combination with proper alignment.

    Args:
        icon (str): Icon key from SEMANTIC_ICONS or direct Font Awesome class
        text (str): Text content
        color (str, optional): Color for both icon and text
        icon_color (str, optional): Color for icon only (overrides color)
        size (str, optional): Size for both icon and text
        icon_size (str, optional): Size for icon only (overrides size)
        icon_position (str): 'left' or 'right'
        className (str, optional): Additional CSS classes
        text_style (dict, optional): Additional text styles
        alignment (str): Vertical alignment (top, center, bottom)
        id (str, optional): Component ID

    Returns:
        html.Div: Icon + text combination with standardized alignment
    """
    # Set alignment style
    alignment_class = {
        "top": "align-items-start",
        "center": "align-items-center",
        "bottom": "align-items-end",
    }.get(alignment, "align-items-center")

    # Create the basic container
    container_class = f"d-flex {alignment_class} {className}"

    # Handle icon color (icon_color overrides color)
    used_icon_color = icon_color if icon_color is not None else color

    # Handle icon size (icon_size overrides size)
    used_icon_size = icon_size if icon_size is not None else size

    # Create the icon
    icon_element = create_icon(
        icon=icon,
        color=used_icon_color,
        size=used_icon_size,
        with_fixed_width=True,
    )

    # Build text style
    text_element_style = {}
    if text_style:
        text_element_style.update(text_style)

    if color:
        text_element_style["color"] = get_color(color)

    # Create text element
    text_element = html.Span(text, style=text_element_style)

    # Position icon and text based on icon_position
    if icon_position == "right":
        content = [text_element, html.Span(icon_element, className="ms-2")]
    else:  # left is default
        content = [html.Span(icon_element, className="me-2"), text_element]

    # Return combined element
    return html.Div(content, className=container_class, id=id)


def create_icon_stack(
    primary_icon,
    secondary_icon,
    primary_color=None,
    secondary_color=None,
    size="md",
    className="",
    id=None,
):
    """
    Create a stacked icon combination (one icon overlaying another).

    Args:
        primary_icon (str): Primary icon class or key
        secondary_icon (str): Secondary icon class or key
        primary_color (str, optional): Color for primary icon
        secondary_color (str, optional): Color for secondary icon
        size (str, optional): Size key from ICON_SIZES
        className (str, optional): Additional CSS classes
        id (str, optional): Component ID

    Returns:
        html.Span: Stacked icon combination
    """
    # Convert size key to numerical value for calculations
    size_value = ICON_SIZES.get(size, ICON_SIZES["md"])
    stack_size = f"calc({size_value} * 2)"

    # Adjust secondary icon size to be slightly smaller
    secondary_size = f"calc({size_value} * 0.65)"

    # Get icon classes
    primary_icon_class = get_icon_class(primary_icon)
    secondary_icon_class = get_icon_class(secondary_icon)

    stack_style = {
        "position": "relative",
        "display": "inline-block",
        "width": stack_size,
        "height": stack_size,
    }

    primary_style = {
        "position": "absolute",
        "top": "0",
        "left": "0",
        "fontSize": size_value,
    }

    secondary_style = {
        "position": "absolute",
        "bottom": "0",
        "right": "0",
        "fontSize": secondary_size,
        "backgroundColor": "white",
        "borderRadius": "50%",
        "padding": "1px",
    }

    if primary_color:
        primary_style["color"] = get_color(primary_color)

    if secondary_color:
        secondary_style["color"] = get_color(secondary_color)

    return html.Span(
        [
            html.I(className=primary_icon_class, style=primary_style),
            html.I(className=secondary_icon_class, style=secondary_style),
        ],
        className=f"icon-stack {className}",
        style=stack_style,
        id=id,
    )


def create_status_icon(
    status, size="md", show_text=False, text=None, className="", id=None
):
    """
    Create a standardized status indicator icon.

    Args:
        status (str): Status type ('success', 'warning', 'danger', 'info')
        size (str, optional): Size key from ICON_SIZES
        show_text (bool): Whether to include status text
        text (str, optional): Custom text (defaults to capitalized status)
        className (str, optional): Additional CSS classes
        id (str, optional): Component ID

    Returns:
        Component: Status icon or icon+text combination
    """
    # Map status to icon and color
    status_map = {
        "success": {"icon": "success", "color": "success"},
        "warning": {"icon": "warning", "color": "warning"},
        "danger": {"icon": "danger", "color": "danger"},
        "error": {"icon": "danger", "color": "danger"},
        "info": {"icon": "info", "color": "info"},
    }

    status_config = status_map.get(status.lower(), status_map["info"])
    display_text = text if text is not None else status.capitalize()

    if show_text:
        return create_icon_text(
            icon=status_config["icon"],
            text=display_text,
            color=status_config["color"],
            size=size,
            className=className,
            id=id,
        )
    else:
        return create_icon(
            icon=status_config["icon"],
            color=status_config["color"],
            size=size,
            className=className,
            id=id,
        )


def create_action_icon(
    action, size="md", color=None, tooltip=None, className="", id=None
):
    """
    Create a standardized action icon.

    Args:
        action (str): Action type ('add', 'edit', 'delete', etc.)
        size (str, optional): Size key from ICON_SIZES
        color (str, optional): Icon color
        tooltip (str, optional): Tooltip text for the icon
        className (str, optional): Additional CSS classes
        id (str, optional): Component ID

    Returns:
        html.I or html.Div: Icon component (with tooltip if specified)
    """
    # Get the appropriate icon class
    icon = action.lower()

    # Create the icon
    icon_element = create_icon(
        icon=icon, color=color, size=size, className=className, id=id
    )

    # Add tooltip if specified
    if tooltip and id:
        from dash import html
        import dash_bootstrap_components as dbc

        return html.Div(
            [icon_element, dbc.Tooltip(tooltip, target=id, placement="top")],
            style={"display": "inline-block"},
        )

    return icon_element
