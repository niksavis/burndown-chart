"""
Style Constants Module

This module contains constants used across different UI modules.
Separating these constants helps prevent circular imports between modules.
"""

#######################################################################
# IMPORTS
#######################################################################
import re
from configuration.settings import COLOR_PALETTE

#######################################################################
# TYPOGRAPHY CONSTANTS
#######################################################################

# Typography system
TYPOGRAPHY = {
    "font_family": "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
    "base_size": "1rem",  # 16px
    "scale": {
        "h1": "2rem",  # 32px
        "h2": "1.75rem",  # 28px
        "h3": "1.5rem",  # 24px
        "h4": "1.25rem",  # 20px
        "h5": "1.1rem",  # ~18px
        "h6": "1rem",  # 16px
        "small": "0.875rem",  # 14px
        "xs": "0.75rem",  # 12px
    },
    "weights": {"light": 300, "regular": 400, "medium": 500, "bold": 700},
}

#######################################################################
# COLOR CONSTANTS
#######################################################################

# Primary color palette (Bootstrap compatible)
PRIMARY_COLORS = {
    "primary": "rgb(13, 110, 253)",  # Bootstrap primary blue
    "teal": "rgb(32, 201, 151)",  # Bootstrap teal
    "orange": "rgb(253, 126, 20)",  # Bootstrap orange
    "purple": "rgb(102, 16, 242)",  # Bootstrap purple
    "pink": "rgb(214, 51, 132)",  # Bootstrap pink
    "indigo": "rgb(102, 16, 242)",  # Bootstrap indigo
}

# Extended semantic color mappings
SEMANTIC_COLORS = {
    "primary": PRIMARY_COLORS["primary"],  # For consistency
    "success": "rgb(40, 167, 69)",  # Bootstrap green
    "warning": "rgb(255, 193, 7)",  # Bootstrap yellow
    "danger": "rgb(220, 53, 69)",  # Bootstrap red
    "info": "rgb(13, 202, 240)",  # Bootstrap cyan
    "secondary": "rgb(108, 117, 125)",  # Bootstrap gray
    "light": "rgb(248, 249, 250)",  # Bootstrap light
    "dark": "rgb(33, 37, 41)",  # Bootstrap dark
}

# Neutral color palette
NEUTRAL_COLORS = {
    "white": "#ffffff",
    "gray-100": "#f8f9fa",
    "gray-200": "#e9ecef",
    "gray-300": "#dee2e6",
    "gray-400": "#ced4da",
    "gray-500": "#adb5bd",
    "gray-600": "#6c757d",
    "gray-700": "#495057",
    "gray-800": "#343a40",
    "gray-900": "#212529",
    "black": "#000000",
}

# Chart and domain-specific colors from settings.py
# Import directly from settings to avoid circular imports
CHART_COLORS = COLOR_PALETTE

#######################################################################
# COLOR UTILITY FUNCTIONS
#######################################################################


def hex_to_rgb(hex_color):
    """
    Convert hex color to RGB format.

    Args:
        hex_color (str): Hex color code (e.g. '#ff0000')

    Returns:
        str: RGB color string (e.g. 'rgb(255, 0, 0)')
    """
    hex_color = hex_color.lstrip("#")
    return f"rgb({int(hex_color[0:2], 16)}, {int(hex_color[2:4], 16)}, {int(hex_color[4:6], 16)})"


def rgb_to_rgba(rgb_color, alpha=1.0):
    """
    Convert RGB color to RGBA format with specified alpha.

    Args:
        rgb_color (str): RGB color string (e.g. 'rgb(255, 0, 0)')
        alpha (float): Alpha transparency value between 0 and 1

    Returns:
        str: RGBA color string (e.g. 'rgba(255, 0, 0, 0.5)')
    """
    if rgb_color.startswith("rgb("):
        rgb_part = rgb_color[4:-1]
        return f"rgba({rgb_part}, {alpha})"
    elif rgb_color.startswith("#"):
        # Handle hex colors
        return rgb_to_rgba(hex_to_rgb(rgb_color), alpha)
    return rgb_color


def parse_rgb_components(rgb_color):
    """
    Parse RGB components from an RGB or RGBA color string.

    Args:
        rgb_color (str): RGB or RGBA color string

    Returns:
        tuple: (r, g, b) components as integers
    """
    if not rgb_color.startswith("rgb"):
        if rgb_color.startswith("#"):
            rgb_color = hex_to_rgb(rgb_color)
        else:
            return (0, 0, 0)  # Default to black on error

    match = re.search(r"rgb a?\((\d+),\s*(\d+),\s*(\d+)", rgb_color)
    if match:
        return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    return (0, 0, 0)  # Default to black on error


def lighten_color(color, amount=0.1):
    """
    Lighten a color by a specified amount.

    Args:
        color (str): RGB or hex color string
        amount (float): Amount to lighten (0-1)

    Returns:
        str: Lightened RGB color
    """
    r, g, b = parse_rgb_components(color)
    r = min(255, int(r + (255 - r) * amount))
    g = min(255, int(g + (255 - g) * amount))
    b = min(255, int(b + (255 - b) * amount))
    return f"rgb({r}, {g}, {b})"


def darken_color(color, amount=0.1):
    """
    Darken a color by a specified amount.

    Args:
        color (str): RGB or hex color string
        amount (float): Amount to darken (0-1)

    Returns:
        str: Darkened RGB color
    """
    r, g, b = parse_rgb_components(color)
    r = max(0, int(r * (1 - amount)))
    g = max(0, int(g * (1 - amount)))
    b = max(0, int(b * (1 - amount)))
    return f"rgb({r}, {g}, {b})"


def get_color_variants(base_color):
    """
    Generate a set of color variants from a base color.

    Args:
        base_color (str): Base RGB or hex color

    Returns:
        dict: Dictionary containing variants of the color
    """
    return {
        "base": base_color,
        "light": lighten_color(base_color, 0.15),
        "lighter": lighten_color(base_color, 0.3),
        "dark": darken_color(base_color, 0.15),
        "darker": darken_color(base_color, 0.3),
        "bg": rgb_to_rgba(base_color, 0.1),  # 10% background
        "border": rgb_to_rgba(base_color, 0.25),  # 25% border
        "focus": rgb_to_rgba(base_color, 0.25),  # 25% focus ring
    }


def create_contrast_color(background_color):
    """
    Create a contrasting text color for a background color.

    Args:
        background_color (str): Background color in RGB or hex format

    Returns:
        str: Either white or black, depending on which has better contrast
    """
    r, g, b = parse_rgb_components(background_color)
    # Calculate luminance (perceived brightness)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    # Return white for dark backgrounds, black for light backgrounds
    return NEUTRAL_COLORS["white"] if luminance < 0.5 else NEUTRAL_COLORS["black"]


#######################################################################
# TOOLTIP CONSTANTS
#######################################################################

# Tooltip styles configuration
TOOLTIP_STYLES = {
    "default": {
        "bgcolor": "rgba(255, 255, 255, 0.95)",
        "bordercolor": "rgba(200, 200, 200, 0.8)",
        "fontcolor": NEUTRAL_COLORS["gray-800"],
        "fontsize": 14,
    },
    "success": {
        "bgcolor": "rgba(240, 255, 240, 0.95)",
        "bordercolor": SEMANTIC_COLORS["success"],
        "fontcolor": NEUTRAL_COLORS["gray-800"],
        "fontsize": 14,
    },
    "warning": {
        "bgcolor": "rgba(255, 252, 235, 0.95)",
        "bordercolor": SEMANTIC_COLORS["warning"],
        "fontcolor": NEUTRAL_COLORS["gray-800"],
        "fontsize": 14,
    },
    "error": {
        "bgcolor": "rgba(255, 235, 235, 0.95)",
        "bordercolor": SEMANTIC_COLORS["danger"],
        "fontcolor": NEUTRAL_COLORS["gray-800"],
        "fontsize": 14,
    },
    "info": {
        "bgcolor": "rgba(235, 250, 255, 0.95)",
        "bordercolor": SEMANTIC_COLORS["info"],
        "fontcolor": NEUTRAL_COLORS["gray-800"],
        "fontsize": 14,
    },
    "primary": {
        "bgcolor": "rgba(235, 245, 255, 0.95)",
        "bordercolor": PRIMARY_COLORS["primary"],
        "fontcolor": NEUTRAL_COLORS["gray-800"],
        "fontsize": 14,
    },
    "dark": {
        "bgcolor": "rgba(33, 37, 41, 0.95)",
        "bordercolor": "rgba(100, 100, 100, 0.8)",
        "fontcolor": NEUTRAL_COLORS["gray-100"],
        "fontsize": 14,
    },
}

# Plotly hover mode settings
HOVER_MODES = {
    "standard": "closest",  # Default Plotly hover mode
    "unified": "x unified",  # Unified x-axis hover
    "compare": "x",  # Compare data points
    "y_unified": "y unified",  # Unified y-axis hover
}
