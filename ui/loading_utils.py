"""
Loading Utilities Module

This module provides a comprehensive set of loading state components
and utilities that can be used across the application to indicate
when content is loading, processing, or waiting for data.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
import warnings

# Third-party library imports
from dash import html
import dash_bootstrap_components as dbc

# Application imports
# Import from configuration if available
try:
    from configuration import COLOR_PALETTE
except ImportError:
    COLOR_PALETTE = {
        "primary": "#0d6efd",
        "secondary": "#6c757d",
        "success": "#198754",
        "info": "#0dcaf0",
        "warning": "#ffc107",
        "danger": "#dc3545",
    }

#######################################################################
# CONSTANTS
#######################################################################

# Loading styles configuration
LOADING_STYLES = {
    "default": {
        "spinner_color": COLOR_PALETTE.get("primary", "#0d6efd"),
        "overlay_color": "rgba(255, 255, 255, 0.8)",
        "text_color": "#212529",  # dark text
        "size": "md",
    },
    "light": {
        "spinner_color": COLOR_PALETTE.get("primary", "#0d6efd"),
        "overlay_color": "rgba(255, 255, 255, 0.9)",
        "text_color": "#212529",  # dark text
        "size": "md",
    },
    "dark": {
        "spinner_color": "#ffffff",  # white
        "overlay_color": "rgba(0, 0, 0, 0.7)",
        "text_color": "#ffffff",  # white
        "size": "md",
    },
    "transparent": {
        "spinner_color": COLOR_PALETTE.get("primary", "#0d6efd"),
        "overlay_color": "rgba(255, 255, 255, 0.4)",
        "text_color": "#212529",  # dark text
        "size": "md",
    },
    "success": {
        "spinner_color": COLOR_PALETTE.get("success", "#198754"),
        "overlay_color": "rgba(255, 255, 255, 0.8)",
        "text_color": COLOR_PALETTE.get("success", "#198754"),
        "size": "md",
    },
    "danger": {
        "spinner_color": COLOR_PALETTE.get("danger", "#dc3545"),
        "overlay_color": "rgba(255, 255, 255, 0.8)",
        "text_color": COLOR_PALETTE.get("danger", "#dc3545"),
        "size": "md",
    },
    "warning": {
        "spinner_color": COLOR_PALETTE.get("warning", "#ffc107"),
        "overlay_color": "rgba(255, 255, 255, 0.8)",
        "text_color": COLOR_PALETTE.get("warning", "#ffc107"),
        "size": "md",
    },
    "info": {
        "spinner_color": COLOR_PALETTE.get("info", "#0dcaf0"),
        "overlay_color": "rgba(255, 255, 255, 0.8)",
        "text_color": COLOR_PALETTE.get("info", "#0dcaf0"),
        "size": "md",
    },
    "primary": {
        "spinner_color": COLOR_PALETTE.get("primary", "#0d6efd"),
        "overlay_color": "rgba(255, 255, 255, 0.8)",
        "text_color": COLOR_PALETTE.get("primary", "#0d6efd"),
        "size": "md",
    },
    "secondary": {
        "spinner_color": COLOR_PALETTE.get("secondary", "#6c757d"),
        "overlay_color": "rgba(255, 255, 255, 0.8)",
        "text_color": COLOR_PALETTE.get("secondary", "#6c757d"),
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
SKELETON_ANIMATION = "@keyframes skeleton-loading { 0% { background-color: rgba(200, 200, 200, 0.2); } 50% { background-color: rgba(200, 200, 200, 0.6); } 100% { background-color: rgba(200, 200, 200, 0.2); } }"

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
    # Base color mapping
    colors = {
        "primary": "#0d6efd",
        "secondary": "#6c757d",
        "success": "#198754",
        "info": "#0dcaf0",
        "warning": "#ffc107",
        "danger": "#dc3545",
        "light": "#f8f9fa",
        "dark": "#212529",
    }

    # Use COLOR_PALETTE if available
    color = COLOR_PALETTE.get(style_key, colors.get(style_key, colors["primary"]))

    # Size mapping
    sizes = {
        "sm": {"width": "1.5rem", "height": "1.5rem", "border-width": "0.15rem"},
        "md": {"width": "2rem", "height": "2rem", "border-width": "0.2rem"},
        "lg": {"width": "3rem", "height": "3rem", "border-width": "0.25rem"},
    }

    size = sizes.get(size_key, sizes["md"])

    # Return combined style
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

    # Default spinner-specific styles
    spinner_style = {
        "borderRadius": "50%",
        "borderStyle": "solid",
        "borderColor": f"{base_style['color']} {base_style['color']} {base_style['color']} transparent",
        "animation": "spinner-border 0.75s linear infinite",
        "display": "inline-block",
    }

    # Combine with base style
    combined_style = {
        "width": base_style["width"],
        "height": base_style["height"],
        "borderWidth": base_style["border-width"],
        **spinner_style,
    }

    # Add any custom styles
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
    Create a spinner loading indicator with optional text.

    Args:
        style_key (str): Color style key (primary, secondary, etc.)
        size_key (str): Size key (sm, md, lg)
        text (str): Optional text to display under the spinner
        className (str): Additional CSS classes
        id (str): Component ID

    Returns:
        html.Div: A spinner component
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
    Create multiple spinner components with a "growing" effect.

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
    # Size mapping is handled by Bootstrap's grow classes
    # We don't need base_style here since we're using Bootstrap's classes directly

    # Size mapping for growing spinners
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

    # Use provided size or default based on size_key
    spinner_props = size_mapping.get(size_key, size_mapping["md"])
    spinner_class = spinner_props["className"]
    spinner_style = spinner_props["style"].copy()

    # Override style with grow_size if provided
    if grow_size:
        spinner_style.update({"width": grow_size, "height": grow_size})

    # Create multiple spinners with staggered animation
    spinners = []
    for i in range(count):
        # Add animation delay based on index
        delay = f"{i * 0.15}s"
        spinner_style_with_delay = {**spinner_style, "animationDelay": delay}

        spinners.append(
            html.Div(
                className=f"{spinner_class} text-{style_key}",
                style=spinner_style_with_delay,
                role="status",
            )
        )

    # Return container with spinners
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
    # Create the Bootstrap spinner component
    spinner = dbc.Spinner(
        type=spinner_type, color=color, size=size, className=className
    )

    if text:
        component = html.Div(
            [spinner, html.Div(text, className="text-center mt-2 text-muted small")],
            className="d-flex flex-column align-items-center justify-content-center py-3",
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

    # Create the spinner for the overlay
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

    # Create content with spinner and text
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


#######################################################################
# SKELETON LOADERS
#######################################################################


def create_skeleton_loader(
    type="text", lines=1, width="100%", height=None, className=""
):
    """
    Create skeleton loading placeholders for content.

    Args:
        type (str): Type of skeleton ('text', 'card', 'circle', 'chart', 'image')
        lines (int): Number of lines for text skeletons
        width (str): Width of the skeleton
        height (str): Height of the skeleton (optional)
        className (str): Additional CSS classes

    Returns:
        html.Div: Skeleton loader component
    """
    base_style = {
        "backgroundColor": "#e9ecef",
        "borderRadius": "0.25rem",
        "animation": "skeleton-loading 1.5s infinite ease-in-out",
    }

    if type == "text":
        # Create multiple text lines with varying widths
        items = []
        for i in range(lines):
            # Make some lines shorter for a more realistic text effect
            line_width = width
            if i == lines - 1:  # Last line
                line_width = "70%" if width == "100%" else width

            items.append(
                html.Div(
                    style={
                        **base_style,
                        "width": line_width,
                        "height": "1rem",
                        "marginBottom": "0.5rem" if i < lines - 1 else "0",
                    }
                )
            )
        return html.Div(items, className=className)

    elif type == "circle":
        # Circular skeleton (for avatars, icons)
        return html.Div(
            style={
                **base_style,
                "width": width,
                "height": width,  # Equal width and height
                "borderRadius": "50%",  # Make it circular
            },
            className=className,
        )

    elif type == "card":
        return html.Div(
            [
                # Card header
                html.Div(
                    style={
                        **base_style,
                        "width": "50%",
                        "height": "1.5rem",
                        "marginBottom": "1rem",
                    }
                ),
                # Card content
                html.Div(
                    [
                        html.Div(
                            style={
                                **base_style,
                                "width": "100%",
                                "height": "0.75rem",
                                "marginBottom": "0.5rem",
                            }
                        )
                        for _ in range(4)
                    ]
                ),
                # Card footer
                html.Div(
                    style={
                        **base_style,
                        "width": "30%",
                        "height": "1rem",
                        "marginTop": "1rem",
                    }
                ),
            ],
            style={
                "width": width,
                "padding": "1rem",
                "border": "1px solid #e9ecef",
                "borderRadius": "0.5rem",
            },
            className=className,
        )

    elif type == "chart":
        # Chart skeleton with axes and bars/lines
        chart_height = height or "200px"

        return html.Div(
            [
                # Y-axis
                html.Div(
                    style={
                        **base_style,
                        "width": "10%",
                        "height": chart_height,
                        "float": "left",
                        "marginRight": "5%",
                    }
                ),
                # Chart content
                html.Div(
                    [
                        html.Div(
                            style={
                                **base_style,
                                "width": "10%",
                                "height": f"{30 + (i * 15 % 40)}%",
                                "display": "inline-block",
                                "marginRight": "5%",
                            }
                        )
                        for i in range(5)
                    ],
                    style={
                        "width": "85%",
                        "height": chart_height,
                        "float": "left",
                        "display": "flex",
                        "alignItems": "flex-end",
                    },
                ),
                # X-axis
                html.Div(
                    style={
                        **base_style,
                        "width": "85%",
                        "height": "10px",
                        "marginTop": "10px",
                        "marginLeft": "15%",
                        "clear": "both",
                    }
                ),
            ],
            style={"width": width, "clear": "both"},
            className=className,
        )

    elif type == "image":
        # Image placeholder
        image_height = height or "200px"

        return html.Div(
            html.Div(
                html.I(className="fas fa-image text-muted"),
                style={
                    "display": "flex",
                    "justifyContent": "center",
                    "alignItems": "center",
                    "height": "100%",
                },
            ),
            style={
                **base_style,
                "width": width,
                "height": image_height,
                "display": "flex",
                "justifyContent": "center",
                "alignItems": "center",
            },
            className=className,
        )

    else:  # Default rectangle
        return html.Div(
            style={**base_style, "width": width, "height": height or "2rem"},
            className=className,
        )


def create_skeleton_chart(type="bar", width="100%", height="300px", className=""):
    """
    Create a skeleton representation of a chart while data is loading.

    Args:
        type (str): Type of chart ('bar', 'line', 'scatter', 'pie')
        width (str): Width of the chart
        height (str): Height of the chart
        className (str): Additional CSS classes

    Returns:
        html.Div: A skeleton chart component
    """
    base_style = {
        "backgroundColor": "#e9ecef",
        "borderRadius": "0.25rem",
        "animation": "skeleton-loading 1.5s infinite ease-in-out",
    }

    if type == "pie":
        # Pie chart skeleton
        return html.Div(
            html.Div(
                style={
                    **base_style,
                    "width": "70%",
                    "height": "70%",
                    "borderRadius": "50%",
                    "margin": "auto",
                }
            ),
            style={"width": width, "height": height, "padding": "15%"},
            className=className,
        )

    elif type == "line":
        # Line chart skeleton
        segments = 8
        return html.Div(
            [
                # Y-axis
                html.Div(
                    style={
                        **base_style,
                        "width": "30px",
                        "height": "calc(100% - 40px)",
                        "position": "absolute",
                        "left": "0",
                        "top": "0",
                    }
                ),
                # Line chart "path"
                html.Div(
                    style={
                        "position": "absolute",
                        "left": "40px",
                        "right": "10px",
                        "top": "30px",
                        "bottom": "40px",
                    },
                    children=[
                        html.Div(
                            style={
                                **base_style,
                                "height": "3px",
                                "width": "100%",
                                "position": "absolute",
                                "top": f"{(50 - (i * 10) % 40)}%",
                                "transform": "translateY(-50%)",
                            }
                        )
                        for i in range(segments - 1)
                    ],
                ),
                # X-axis
                html.Div(
                    style={
                        **base_style,
                        "width": "calc(100% - 40px)",
                        "height": "30px",
                        "position": "absolute",
                        "left": "40px",
                        "bottom": "0",
                    }
                ),
            ],
            style={"width": width, "height": height, "position": "relative"},
            className=className,
        )

    else:  # Default bar chart
        # Bar chart skeleton
        bars = 6
        return html.Div(
            [
                # Y-axis
                html.Div(
                    style={
                        **base_style,
                        "width": "30px",
                        "height": "calc(100% - 40px)",
                        "position": "absolute",
                        "left": "0",
                        "top": "0",
                    }
                ),
                # Bars
                html.Div(
                    style={
                        "position": "absolute",
                        "left": "40px",
                        "right": "10px",
                        "top": "0",
                        "bottom": "40px",
                        "display": "flex",
                        "alignItems": "flex-end",
                    },
                    children=[
                        html.Div(
                            style={
                                **base_style,
                                "width": f"calc({100 / bars}% - 10px)",
                                "height": f"{20 + (i * 15) % 60}%",
                                "margin": "0 5px",
                            }
                        )
                        for i in range(bars)
                    ],
                ),
                # X-axis
                html.Div(
                    style={
                        **base_style,
                        "width": "calc(100% - 40px)",
                        "height": "30px",
                        "position": "absolute",
                        "left": "40px",
                        "bottom": "0",
                    }
                ),
            ],
            style={"width": width, "height": height, "position": "relative"},
            className=className,
        )


#######################################################################
# CONTENT PLACEHOLDERS
#######################################################################


def create_content_placeholder(type="data", text=None, icon=None, className=""):
    """
    Create a placeholder for content that hasn't loaded yet.

    Args:
        type (str): Type of content ('data', 'chart', 'table', 'image')
        text (str): Message to display in the placeholder
        icon (str): FontAwesome icon class (overrides default icon)
        className (str): Additional CSS classes

    Returns:
        html.Div: A content placeholder component
    """
    # Default settings by type
    type_defaults = {
        "data": {
            "icon": "fas fa-database",
            "message": "Loading data...",
            "color": "#6c757d",  # secondary
        },
        "chart": {
            "icon": "fas fa-chart-bar",
            "message": "Preparing chart...",
            "color": "#0d6efd",  # primary
        },
        "table": {
            "icon": "fas fa-table",
            "message": "Loading table data...",
            "color": "#198754",  # success
        },
        "image": {
            "icon": "fas fa-image",
            "message": "Loading image...",
            "color": "#0dcaf0",  # info
        },
        "file": {
            "icon": "fas fa-file-alt",
            "message": "Loading file...",
            "color": "#ffc107",  # warning
        },
        "form": {
            "icon": "fas fa-wpforms",
            "message": "Preparing form...",
            "color": "#6c757d",  # secondary
        },
    }

    # Get defaults for the specified type or use generic data defaults
    defaults = type_defaults.get(type, type_defaults["data"])

    # Use provided text and icon or fall back to defaults
    display_text = text if text is not None else defaults["message"]
    display_icon = icon if icon is not None else defaults["icon"]

    return html.Div(
        [
            html.I(
                className=f"{display_icon} fa-3x mb-3",
                style={"color": defaults["color"], "opacity": "0.7"},
            ),
            html.Div(display_text, className="text-muted"),
        ],
        className=f"d-flex flex-column justify-content-center align-items-center py-5 {className}",
        style={
            "backgroundColor": "#f8f9fa",
            "border": "1px dashed #dee2e6",
            "borderRadius": "0.5rem",
            "minHeight": "200px",
        },
    )


#######################################################################
# HIGH-LEVEL LOADING COMPONENTS
#######################################################################


def create_loading_indicator(
    id="loading", type="spinner", message="Loading...", color="primary", size="md"
):
    """
    DEPRECATED: Use the specific loading components instead.
    This function will be removed in a future release.

    Create a standardized loading indicator component.

    Args:
        id (str): Component ID
        type (str): Type of indicator (spinner, growing, skeleton)
        message (str): Message to display while loading
        color (str): Bootstrap color variant
        size (str): Size of the loading indicator (sm, md, lg)

    Returns:
        Dash component: A loading indicator component
    """
    warnings.warn(
        "create_loading_indicator is deprecated. Use create_spinner, create_growing_spinner, or create_skeleton_loader instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    if type == "skeleton":
        return create_skeleton_loader(
            type="text", lines=3, className="mb-3", width="100%"
        )

    elif type == "growing":
        return create_growing_spinner(
            style_key=color, size_key=size, text=message, id=id
        )

    else:  # Default spinner
        return create_spinner(
            style_key=color, size_key=size, text=message, className="my-3", id=id
        )


def create_loading_wrapper(
    children,
    is_loading=False,
    id=None,
    type="overlay",
    color="primary",
    size="md",
    message="Loading...",
):
    """
    DEPRECATED: Use specific loading components like create_loading_overlay,
    create_skeleton_loader, or create_content_placeholder instead.
    This function will be removed in a future release.

    Wrap content with a loading indicator.

    Args:
        children: Content to display when not loading
        is_loading (bool): Whether to show the loading state
        id (str): Component ID
        type (str): Type of loading wrapper (overlay, skeleton, placeholder)
        color (str): Color variant for the loading indicator
        size (str): Size of the loading indicator
        message (str): Loading message to display

    Returns:
        Dash component: A component that shows a loading state or the children
    """
    warnings.warn(
        "create_loading_wrapper is deprecated. Use create_loading_overlay, create_skeleton_loader, or create_content_placeholder instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    content_id = f"{id}-content" if id else None

    if type == "overlay":
        return create_loading_overlay(
            children=children,
            style_key=color,
            size_key=size,
            text=message,
            is_loading=is_loading,
        )

    elif type == "skeleton":
        if is_loading:
            # For skeleton loading, we'll create multiple lines based on content size estimate
            return html.Div(
                [
                    create_skeleton_loader(type="card", width="100%"),
                ],
                id=content_id,
            )
        else:
            return html.Div(children, id=content_id)

    elif type == "placeholder":
        if is_loading:
            return create_content_placeholder(
                type="chart" if "chart" in str(children).lower() else "data",
                text=message,
                className="my-3",
            )
        else:
            return html.Div(children, id=content_id)

    else:  # Simple loading indicator without an overlay
        if is_loading:
            return html.Div(
                create_loading_indicator(
                    type="spinner", message=message, color=color, size=size
                ),
                className="d-flex justify-content-center my-4",
            )
        else:
            return html.Div(children, id=content_id)


def create_loading_state(
    children=None,
    is_loading=False,
    type="spinner",  # spinner, growing, skeleton, overlay, placeholder
    style_key="primary",
    size_key="md",
    message="Loading...",
    className="",
    id=None,
):
    """
    Unified loading state component that provides a consistent interface
    for all loading state types.

    Args:
        children: Content to display when not loading (required for overlay type)
        is_loading (bool): Whether to show the loading state
        type (str): Type of loading component ('spinner', 'growing', 'skeleton', 'overlay', 'placeholder')
        style_key (str): Color style key (primary, secondary, success, etc.)
        size_key (str): Size key (xs, sm, md, lg, xl)
        message (str): Message to display with the loading indicator
        className (str): Additional CSS classes
        id (str): Component ID

    Returns:
        Dash component: A loading state component of the specified type
    """
    # If not loading and we have children, just return the children
    if not is_loading and children is not None:
        return html.Div(children, className=className, id=id)

    if type == "spinner":
        return create_spinner(
            style_key=style_key,
            size_key=size_key,
            text=message,
            className=className,
            id=id,
        )

    elif type == "growing":
        return create_growing_spinner(
            style_key=style_key,
            size_key=size_key,
            text=message,
            className=className,
            id=id,
        )

    elif type == "skeleton":
        # Determine skeleton type based on children or default to "text"
        skeleton_type = "text"
        if children is not None:
            children_str = str(children).lower()
            if "chart" in children_str or "graph" in children_str:
                skeleton_type = "chart"
            elif "card" in children_str:
                skeleton_type = "card"
            elif "img" in children_str or "image" in children_str:
                skeleton_type = "image"

        return create_skeleton_loader(
            type=skeleton_type,
            lines=3 if skeleton_type == "text" else 1,
            className=className,
        )

    elif type == "overlay":
        if children is None:
            raise ValueError("Children must be provided when using 'overlay' type")

        return create_loading_overlay(
            children=children,
            style_key=style_key,
            size_key=size_key,
            text=message,
            is_loading=is_loading,
            className=className,
        )

    elif type == "placeholder":
        # Determine placeholder type based on children or default to "data"
        placeholder_type = "data"
        if children is not None:
            children_str = str(children).lower()
            if "chart" in children_str or "graph" in children_str:
                placeholder_type = "chart"
            elif "table" in children_str:
                placeholder_type = "table"
            elif "img" in children_str or "image" in children_str:
                placeholder_type = "image"

        return create_content_placeholder(
            type=placeholder_type, text=message, className=className
        )

    else:
        # Invalid type, return default spinner
        warnings.warn(
            f"Invalid loading type '{type}'. Using default spinner.",
            UserWarning,
            stacklevel=2,
        )
        return create_spinner(
            style_key=style_key,
            size_key=size_key,
            text=message,
            className=className,
            id=id,
        )


def create_async_content(id, loading_state_id=None, content_type="chart"):
    """
    Create a container for async content with proper loading states.

    Args:
        id (str): ID for the component
        loading_state_id (str): ID for the loading state indicator, defaults to {id}-loading
        content_type (str): Type of content ('chart', 'data', 'table', etc.)

    Returns:
        html.Div: Container with loading placeholder
    """
    if loading_state_id is None:
        loading_state_id = f"{id}-loading"

    # Determine appropriate loading message
    loading_messages = {
        "chart": "Loading chart data...",
        "table": "Loading table data...",
        "data": "Loading data...",
        "image": "Loading image...",
    }

    message = loading_messages.get(content_type, "Loading...")

    return html.Div(
        [
            # Hidden loading state that can be triggered by callbacks
            html.Div(id=loading_state_id, style={"display": "none"}),
            # Initial placeholder
            create_content_placeholder(type=content_type, text=message),
            # Container for the actual content (empty initially)
            html.Div(id=id),
        ]
    )


def create_lazy_loading_tabs(
    tabs_data, tab_id_prefix="tab", content_id_prefix="tab-content"
):
    """
    Create tabs that load their content only when activated.

    Args:
        tabs_data (list): List of dictionaries with tab information:
                          [{"label": "Tab1", "content": content1, "active": True}, ...]
        tab_id_prefix (str): Prefix for tab IDs
        content_id_prefix (str): Prefix for content IDs

    Returns:
        list: A list containing the tabs component and the tab content div
    """
    tabs = []
    contents = []

    # Create each tab
    for i, tab in enumerate(tabs_data):
        tab_id = f"{tab_id_prefix}-{i}"
        content_id = f"{content_id_prefix}-{i}"

        # Create the tab
        tabs.append(
            dbc.Tab(
                label=tab["label"],
                tab_id=tab_id,
                active=tab.get("active", i == 0),
                id=tab_id,
            )
        )

        # Create the content container
        content_div = html.Div(
            # If it's the active tab, show content, otherwise show a placeholder
            tab["content"]
            if tab.get("active", i == 0)
            else create_content_placeholder(
                type=tab.get("content_type", "data"),
                text=f"Loading {tab['label']}...",
            ),
            id=content_id,
            style={"display": "block" if tab.get("active", i == 0) else "none"},
        )

        contents.append(content_div)

    return [
        dbc.Tabs(tabs, id=f"{tab_id_prefix}-container"),
        html.Div(contents, id=f"{content_id_prefix}-container"),
    ]


def create_data_loading_section(
    id,
    title=None,
    loading_message="Loading data...",
    error_message="Failed to load data",
    retry_button=True,
):
    """
    Create a section that handles data loading states including error handling.

    Args:
        id (str): Base ID for the section
        title (str): Optional title for the section
        loading_message (str): Message to display during loading
        error_message (str): Message to display on error
        retry_button (bool): Whether to show a retry button on error

    Returns:
        html.Div: A complete section with loading and error states
    """
    section_id = f"{id}-section"
    loading_id = f"{id}-loading"
    content_id = f"{id}-content"
    error_id = f"{id}-error"
    retry_id = f"{id}-retry"

    header = html.H5(title) if title else None

    return html.Div(
        [
            header,
            # Loading state (hidden initially)
            html.Div(
                create_loading_state(
                    message=loading_message, type="spinner", style_key="primary"
                ),
                id=loading_id,
                style={"display": "none"},
            ),
            # Content container (empty initially)
            html.Div(id=content_id),
            # Error state (hidden initially)
            html.Div(
                [
                    html.Div(
                        [
                            html.I(
                                className="fas fa-exclamation-triangle text-danger me-2"
                            ),
                            html.Span(error_message),
                        ],
                        className="d-flex align-items-center mb-3",
                    ),
                    html.Button(
                        "Retry",
                        id=retry_id,
                        className="btn btn-outline-primary btn-sm",
                    )
                    if retry_button
                    else None,
                ],
                id=error_id,
                className="my-4 p-3 border border-danger rounded",
                style={"display": "none"},
            ),
        ],
        id=section_id,
        className="mb-4",
    )
