"""
Loading Utilities Core Module

Base loading overlay, spinner, and skeleton functions providing
the foundational loading state components for the application.
"""

#######################################################################
# IMPORTS
#######################################################################
import dash_bootstrap_components as dbc

# Third-party library imports
from dash import html

# Application imports
from ui._loading_skeleton import create_skeleton_loader  # noqa: F401
from ui.style_constants import (
    NEUTRAL_COLORS,
    PRIMARY_COLORS,
    SEMANTIC_COLORS,
)

#######################################################################
# CONSTANTS
#######################################################################

# Loading styles configuration
LOADING_STYLES = {
    "default": {
        "spinner_color": PRIMARY_COLORS.get("primary"),
        "overlay_color": "rgba(255, 255, 255, 0.8)",
        "text_color": NEUTRAL_COLORS.get("gray-900"),  # dark text
        "size": "md",
    },
    "light": {
        "spinner_color": PRIMARY_COLORS.get("primary"),
        "overlay_color": "rgba(255, 255, 255, 0.9)",
        "text_color": NEUTRAL_COLORS.get("gray-900"),  # dark text
        "size": "md",
    },
    "dark": {
        "spinner_color": NEUTRAL_COLORS.get("white"),  # white
        "overlay_color": "rgba(0, 0, 0, 0.7)",
        "text_color": NEUTRAL_COLORS.get("white"),  # white
        "size": "md",
    },
    "transparent": {
        "spinner_color": PRIMARY_COLORS.get("primary"),
        "overlay_color": "rgba(255, 255, 255, 0.4)",
        "text_color": NEUTRAL_COLORS.get("gray-900"),  # dark text
        "size": "md",
    },
    "success": {
        "spinner_color": SEMANTIC_COLORS.get("success"),
        "overlay_color": "rgba(255, 255, 255, 0.8)",
        "text_color": SEMANTIC_COLORS.get("success"),
        "size": "md",
    },
    "danger": {
        "spinner_color": SEMANTIC_COLORS.get("danger"),
        "overlay_color": "rgba(255, 255, 255, 0.8)",
        "text_color": SEMANTIC_COLORS.get("danger"),
        "size": "md",
    },
    "warning": {
        "spinner_color": SEMANTIC_COLORS.get("warning"),
        "overlay_color": "rgba(255, 255, 255, 0.8)",
        "text_color": SEMANTIC_COLORS.get("warning"),
        "size": "md",
    },
    "info": {
        "spinner_color": SEMANTIC_COLORS.get("info"),
        "overlay_color": "rgba(255, 255, 255, 0.8)",
        "text_color": SEMANTIC_COLORS.get("info"),
        "size": "md",
    },
    "primary": {
        "spinner_color": PRIMARY_COLORS.get("primary"),
        "overlay_color": "rgba(255, 255, 255, 0.8)",
        "text_color": PRIMARY_COLORS.get("primary"),
        "size": "md",
    },
    "secondary": {
        "spinner_color": SEMANTIC_COLORS.get("secondary"),
        "overlay_color": "rgba(255, 255, 255, 0.8)",
        "text_color": SEMANTIC_COLORS.get("secondary"),
        "size": "md",
    },
}

# Spinner size configuration
SPINNER_SIZES = {
    "xs": {"width": "1rem", "height": "1rem", "border_width": "0.15rem"},
    "sm": {"width": "1.5rem", "height": "1.5rem", "border_width": "0.2rem"},
    "md": {"width": "2rem", "height": "2rem", "border_width": "0.25rem"},
    "lg": {"width": "3rem", "height": "3rem", "border_width": "0.3rem"},
    "xl": {"width": "4rem", "height": "4rem", "border_width": "0.35rem"},
}

# CSS animation for skeleton loaders
SKELETON_ANIMATION = (
    "@keyframes skeleton-loading { "
    "0% { background-color: rgba(200, 200, 200, 0.2); } "
    "50% { background-color: rgba(200, 200, 200, 0.6); } "
    "100% { background-color: rgba(200, 200, 200, 0.2); } "
    "}"
)

#######################################################################
# LOADING STYLE UTILITIES
#######################################################################


def get_loading_style(style_key="primary", size_key="md"):
    """
    Get standardized styling for loading indicators.

    Args:
        style_key (str): Color style key (primary, secondary, success, etc.)
        size_key (str): Size key (sm, md, lg)

    Returns:
        dict: Dictionary of style attributes
    """
    colors = {
        "primary": PRIMARY_COLORS.get("primary"),
        "secondary": SEMANTIC_COLORS.get("secondary"),
        "success": SEMANTIC_COLORS.get("success"),
        "info": SEMANTIC_COLORS.get("info"),
        "warning": SEMANTIC_COLORS.get("warning"),
        "danger": SEMANTIC_COLORS.get("danger"),
        "light": NEUTRAL_COLORS.get("gray-100"),
        "dark": NEUTRAL_COLORS.get("gray-900"),
    }

    color = colors.get(style_key, colors["primary"])

    sizes = {
        "sm": {"width": "1.5rem", "height": "1.5rem", "border-width": "0.15rem"},
        "md": {"width": "2rem", "height": "2rem", "border-width": "0.2rem"},
        "lg": {"width": "3rem", "height": "3rem", "border-width": "0.25rem"},
    }

    size = sizes.get(size_key, sizes["md"])

    return {"color": color, **size}


def create_spinner_style(style_key="primary", size_key="md", custom_style=None):
    """
    Create CSS style for spinner components.

    Args:
        style_key (str): Color style key
        size_key (str): Size key (sm, md, lg)
        custom_style (dict): Additional custom styles to apply

    Returns:
        dict: Dictionary of CSS styles for the spinner
    """
    base_style = get_loading_style(style_key, size_key)

    spinner_style = {
        "borderRadius": "50%",
        "borderStyle": "solid",
        "borderColor": (
            f"{base_style['color']} {base_style['color']}"
            f" {base_style['color']} transparent"
        ),
        "animation": "spinner-border 0.75s linear infinite",
        "display": "inline-block",
    }

    combined_style = {
        "width": base_style["width"],
        "height": base_style["height"],
        "borderWidth": base_style["border-width"],
        **spinner_style,
    }

    if custom_style:
        combined_style.update(custom_style)

    return combined_style


#######################################################################
# SPINNER COMPONENTS
#######################################################################


def create_spinner(
    style_key="primary", size_key="md", text=None, className="", id=None
):
    """
    Creates a Bootstrap spinner component.

    Args:
        style_key (str, optional): The color style of the spinner
            (e.g., "primary", "secondary"). Defaults to "primary".
        size_key (str, optional): The size of the spinner
            ("sm", "md", "lg"). Defaults to "md".
        text (str, optional): Optional text to display alongside
            the spinner. Defaults to None.
        className (str, optional): Additional CSS classes to apply. Defaults to "".

    Returns:
        html.Div: A Div containing the spinner and optional text.
    """
    spinner_style = create_spinner_style(style_key, size_key)

    spinner = html.Div(
        style=spinner_style,
        className="spinner-border" + (f" {className}" if className else ""),
    )

    if text:
        return html.Div(
            [spinner, html.Div(text, className="text-center mt-2 text-muted small")],
            className="d-flex flex-column align-items-center justify-content-center",
            id=id,
        )
    else:
        return html.Div(
            spinner,
            className="d-flex justify-content-center"
            + (f" {className}" if className else ""),
            id=id,
        )


def create_growing_spinner(
    style_key="primary",
    size_key="md",
    grow_size=None,
    count=3,
    variant="circle",
    className="",
):
    """
    Create multiple spinner components with a growing effect.

    Args:
        style_key (str): Style/color variant
        size_key (str): Size of the spinners (sm, md, lg)
        grow_size (str): Size of the growing effect (overrides size_key)
        count (int): Number of spinners to show
        variant (str): Spinner variant (circle, dot)
        className (str): Additional CSS classes

    Returns:
        html.Div: A component with multiple growing spinners
    """
    size_mapping = {
        "xs": {
            "className": "spinner-grow spinner-grow-sm",
            "style": {"width": "0.5rem", "height": "0.5rem"},
        },
        "sm": {"className": "spinner-grow spinner-grow-sm", "style": {}},
        "md": {"className": "spinner-grow", "style": {}},
        "lg": {
            "className": "spinner-grow",
            "style": {"width": "2rem", "height": "2rem"},
        },
        "xl": {
            "className": "spinner-grow",
            "style": {"width": "3rem", "height": "3rem"},
        },
    }

    spinner_props = size_mapping.get(size_key, size_mapping["md"])
    spinner_class = spinner_props["className"]
    spinner_style = spinner_props["style"].copy()

    if grow_size:
        spinner_style.update({"width": grow_size, "height": grow_size})

    spinners = []
    for i in range(count):
        delay = f"{i * 0.15}s"
        spinner_style_with_delay = {**spinner_style, "animationDelay": delay}

        spinners.append(
            html.Div(
                className=f"{spinner_class} text-{style_key}",
                style=spinner_style_with_delay,
                role="status",
            )
        )

    return html.Div(
        spinners,
        className=f"d-flex align-items-center justify-content-center gap-2 {className}",
    )


def create_bootstrap_spinner(
    spinner_type="border",
    color="primary",
    size=None,
    text=None,
    centered=True,
    className="",
):
    """
    Create a Bootstrap spinner component.

    Args:
        spinner_type (str): Type of spinner ('border' or 'grow')
        color (str): Bootstrap color name
        size (str): Size ('sm' or None for default)
        text (str): Optional text to display with the spinner
        centered (bool): Whether to center the spinner
        className (str): Additional CSS classes

    Returns:
        dbc.Spinner or html.Div: Bootstrap spinner component
    """
    spinner = dbc.Spinner(
        type=spinner_type, color=color, size=size, className=className
    )

    if text:
        component = html.Div(
            [spinner, html.Div(text, className="text-center mt-2 text-muted small")],
            className=(
                "d-flex flex-column align-items-center justify-content-center py-3"
            ),
        )
    else:
        component = spinner

    if centered:
        return html.Div(component, className="d-flex justify-content-center")
    else:
        return component


#######################################################################
# LOADING OVERLAYS
#######################################################################


def create_loading_overlay(
    children,
    style_key="primary",
    size_key="md",
    text=None,
    is_loading=False,
    opacity=0.7,
    className="",
):
    """
    Create a loading overlay that covers content while loading.

    Args:
        children: Content to display when not loading
        style_key (str): Color style for the spinner
        size_key (str): Size of the spinner
        text (str): Optional text to display during loading
        is_loading (bool): Whether to show the loading state
        opacity (float): Opacity of the overlay background
        className (str): Additional CSS classes

    Returns:
        html.Div: A component with loading overlay
    """
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

    spinner = create_spinner(style_key, size_key, text)

    return html.Div(
        [
            html.Div(  # Overlay with spinner
                spinner, style=overlay_style
            ),
            html.Div(  # Content (blurred or dimmed during loading)
                children, style={"filter": "blur(1px)"}
            ),
        ],
        style={"position": "relative"},
        className=className,
    )


def create_fullscreen_loading(
    style_key="primary",
    size_key="lg",
    text="Loading...",
    show=False,
    backdrop_opacity=0.7,
    blur=False,
    id=None,
):
    """
    Create a fullscreen loading overlay for major loading operations.

    Args:
        style_key (str): Color style key
        size_key (str): Size key
        text (str): Text to display with the spinner
        show (bool): Whether to display the overlay
        backdrop_opacity (float): Opacity of the backdrop
        blur (bool): Whether to apply blur effect to background
        id (str): Component ID

    Returns:
        html.Div: A fullscreen loading overlay
    """
    if not show:
        return html.Div(id=id, style={"display": "none"})

    backdrop_style = {
        "position": "fixed",
        "top": "0",
        "left": "0",
        "width": "100vw",
        "height": "100vh",
        "backgroundColor": f"rgba(0, 0, 0, {backdrop_opacity})",
        "display": "flex",
        "justifyContent": "center",
        "alignItems": "center",
        "zIndex": "2000",
        "backdropFilter": "blur(5px)" if blur else "none",
    }

    content = html.Div(
        [
            create_spinner(style_key, size_key),
            html.Div(
                text,
                className="text-center mt-3 text-white",
                style={"fontSize": "1.2rem"},
            ),
        ],
        className="d-flex flex-column align-items-center",
    )

    return html.Div(content, style=backdrop_style, id=id)
