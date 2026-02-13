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
# Default variant uses dark/blackish background for better readability
TOOLTIP_STYLES = {
    "default": {
        "bgcolor": "rgba(33, 37, 41, 0.95)",  # Dark/blackish background
        "bordercolor": "rgba(255, 255, 255, 0.1)",
        "fontcolor": NEUTRAL_COLORS["gray-100"],  # Light text for contrast
        "fontsize": 14,
    },
    "dark": {
        "bgcolor": "rgba(33, 37, 41, 0.95)",  # Dark/blackish background
        "bordercolor": "rgba(255, 255, 255, 0.1)",
        "fontcolor": NEUTRAL_COLORS["gray-100"],  # Light text for contrast
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
}

# Plotly hover mode settings
HOVER_MODES = {
    "standard": "closest",  # Default Plotly hover mode
    "unified": "x unified",  # Unified x-axis hover
    "compare": "x",  # Compare data points
    "y_unified": "y unified",  # Unified y-axis hover
}


#######################################################################
# METRIC CARD CONSTANTS (Unified Design System)
#######################################################################

# Metric card design tokens - based on Bug Analysis Dashboard style
METRIC_CARD = {
    "icon_size": "36px",
    "icon_circle_size": "36px",
    "icon_bg": "white",
    "padding": "0.75rem",
    "border_radius": "8px",
    "border_width": "1px",
    "margin_bottom": "0.5rem",
    "min_height": "120px",  # Ensures equal height cards
}

# Status-based color schemes for metric indicators
METRIC_STATUS_COLORS = {
    "excellent": {
        "primary": "#28a745",  # Green
        "bg": "rgba(40, 167, 69, 0.1)",
        "border": "rgba(40, 167, 69, 0.2)",
        "icon": "fa-check-circle",
    },
    "good": {
        "primary": "#ffc107",  # Yellow
        "bg": "rgba(255, 193, 7, 0.1)",
        "border": "rgba(255, 193, 7, 0.2)",
        "icon": "fa-check-circle",
    },
    "warning": {
        "primary": "#fd7e14",  # Orange
        "bg": "rgba(253, 126, 20, 0.1)",
        "border": "rgba(253, 126, 20, 0.2)",
        "icon": "fa-exclamation-triangle",
    },
    "danger": {
        "primary": "#dc3545",  # Red
        "bg": "rgba(220, 53, 69, 0.1)",
        "border": "rgba(220, 53, 69, 0.2)",
        "icon": "fa-exclamation-circle",
    },
    "info": {
        "primary": "#20c997",  # Teal
        "bg": "rgba(32, 201, 151, 0.1)",
        "border": "rgba(32, 201, 151, 0.2)",
        "icon": "fa-info-circle",
    },
    "neutral": {
        "primary": "#6c757d",  # Gray
        "bg": "rgba(108, 117, 125, 0.1)",
        "border": "rgba(108, 117, 125, 0.2)",
        "icon": "fa-equals",
    },
}

# Responsive breakpoints for metric cards
METRIC_CARD_BREAKPOINTS = {
    "mobile": 12,  # Full width on mobile (col-12)
    "tablet": 6,  # 2 columns on tablet (col-md-6)
    "desktop": 4,  # 3 columns on desktop (col-md-4)
    "wide": 3,  # 4 columns on wide screens (col-lg-3)
}


#######################################################################
# HELP ICON CONSTANTS (Unified Positioning)
#######################################################################

# Help/tooltip icon standardization
HELP_ICON = {
    "class": "fas fa-info-circle",
    "color": "#3b82f6",  # Brand blue (updated from #17a2b8)
    "size": "0.875rem",  # 14px
    "margin_left": "0.5rem",
    "cursor": "pointer",
    "position": "inline",  # Can be 'inline', 'header', or 'trailing'
}

# Help icon positioning patterns
HELP_ICON_POSITIONS = {
    "inline": {
        "class": "ms-1",  # Margin start 1
        "vertical_align": "middle",
    },
    "header": {
        "class": "ms-2",
        "vertical_align": "text-top",
    },
    "trailing": {
        "class": "ms-auto",  # Push to end
        "vertical_align": "middle",
    },
}


#######################################################################
# COMPREHENSIVE DESIGN TOKENS (Phase 2 Enhancement)
#######################################################################

# Complete design system following Bootstrap 5 FLATLY theme
DESIGN_TOKENS = {
    # ========== COLORS ==========
    "colors": {
        # Primary palette
        "primary": "#0d6efd",
        "secondary": "#6c757d",
        "success": "#198754",
        "warning": "#ffc107",
        "danger": "#dc3545",
        "info": "#0dcaf0",
        "light": "#f8f9fa",
        "dark": "#343a40",
        # Neutrals
        "white": "#ffffff",
        "black": "#000000",
        "gray-100": "#f8f9fa",
        "gray-200": "#e9ecef",
        "gray-300": "#dee2e6",
        "gray-400": "#ced4da",
        "gray-500": "#adb5bd",
        "gray-600": "#6c757d",
        "gray-700": "#495057",
        "gray-800": "#343a40",
        "gray-900": "#212529",
        # Interactive states
        "primary-hover": "#0b5ed7",
        "primary-active": "#0a58ca",
        "focus-shadow": "rgba(13, 110, 253, 0.25)",
        # Extended palette
        "teal": "#20c997",
        "orange": "#fd7e14",
        "purple": "#6610f2",
        "pink": "#d63384",
        "indigo": "#6610f2",
        "cyan": "#0dcaf0",
    },
    # ========== SPACING ==========
    "spacing": {
        "xs": "0.25rem",  # 4px
        "sm": "0.5rem",  # 8px
        "md": "1rem",  # 16px
        "lg": "1.5rem",  # 24px
        "xl": "2rem",  # 32px
        "xxl": "3rem",  # 48px
        "xxxl": "4rem",  # 64px
    },
    # ========== TYPOGRAPHY ==========
    "typography": {
        "fontFamily": "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
        "size": {
            "xs": "0.75rem",  # 12px
            "sm": "0.875rem",  # 14px
            "base": "1rem",  # 16px
            "lg": "1.125rem",  # 18px
            "xl": "1.25rem",  # 20px
            "2xl": "1.5rem",  # 24px
            "3xl": "1.875rem",  # 30px
            "4xl": "2.25rem",  # 36px
        },
        "weight": {
            "light": 300,
            "normal": 400,
            "medium": 500,
            "semibold": 600,
            "bold": 700,
        },
        "lineHeight": {
            "tight": 1.2,
            "base": 1.5,
            "relaxed": 1.75,
            "loose": 2.0,
        },
    },
    # ========== LAYOUT ==========
    "layout": {
        "borderRadius": {
            "sm": "0.25rem",  # 4px
            "md": "0.375rem",  # 6px
            "lg": "0.5rem",  # 8px
            "xl": "0.75rem",  # 12px
            "full": "9999px",  # Pill shape
        },
        "shadow": {
            "sm": "0 .125rem .25rem rgba(0,0,0,.075)",
            "md": "0 .5rem 1rem rgba(0,0,0,.15)",
            "lg": "0 1rem 3rem rgba(0,0,0,.175)",
            "none": "none",
        },
        "zIndex": {
            "base": 1,
            "dropdown": 1000,
            "sticky": 1020,
            "fixed": 1030,
            "modal-backdrop": 1040,
            "modal": 1050,
            "popover": 1060,
            "tooltip": 1070,
        },
        "borderWidth": {
            "thin": "1px",
            "medium": "2px",
            "thick": "4px",
        },
    },
    # ========== ANIMATION ==========
    "animation": {
        "duration": {
            "instant": "100ms",
            "fast": "200ms",
            "base": "300ms",
            "slow": "500ms",
            "slower": "700ms",
        },
        "easing": {
            "default": "ease-in-out",
            "smooth": "cubic-bezier(0.4, 0.0, 0.2, 1)",
            "ease-in": "ease-in",
            "ease-out": "ease-out",
            "linear": "linear",
        },
    },
    # ========== RESPONSIVE BREAKPOINTS ==========
    "breakpoints": {
        "xs": "0px",  # Extra small devices
        "sm": "576px",  # Small devices (landscape phones)
        "md": "768px",  # Medium devices (tablets)
        "lg": "992px",  # Large devices (desktops)
        "xl": "1200px",  # Extra large devices (large desktops)
        "xxl": "1400px",  # Extra extra large devices
    },
    # ========== COMPONENT-SPECIFIC ==========
    "components": {
        "button": {
            "paddingY": "0.375rem",
            "paddingX": "0.75rem",
            "fontSize": "1rem",
            "borderRadius": "0.375rem",
            "minWidth": "44px",  # Touch target minimum
            "minHeight": "44px",  # Touch target minimum
        },
        "card": {
            "padding": "1rem",
            "borderRadius": "0.375rem",
            "shadow": "0 .125rem .25rem rgba(0,0,0,.075)",
            "borderWidth": "1px",
            "headerPadding": "0.75rem 1rem",
            "footerPadding": "0.75rem 1rem",
        },
        "input": {
            "padding": "0.375rem 0.75rem",
            "fontSize": "1rem",
            "borderRadius": "0.375rem",
            "borderWidth": "1px",
            "focusBorderColor": "#0d6efd",
            "focusShadow": "0 0 0 0.25rem rgba(13, 110, 253, 0.25)",
            "minHeight": "44px",  # Touch target minimum
        },
        "tab": {
            "padding": "0.5rem 1rem",
            "borderRadius": "0.375rem 0.375rem 0 0",
            "activeBg": "#0d6efd",
            "activeBorder": "#0d6efd",
            "activeColor": "#ffffff",
            "hoverBg": "rgba(13, 110, 253, 0.1)",
        },
    },
    # ========== MOBILE-SPECIFIC ==========
    "mobile": {
        "touchTargetMin": "44px",  # Minimum touch target size
        "bottomSheetMaxHeight": "80vh",
        "navBarHeight": "56px",
        "fabSize": "56px",
        "fabPosition": "16px",  # Distance from edge
        "swipeThreshold": "50px",  # Minimum swipe distance
    },
}


#######################################################################
# DESIGN TOKEN HELPER FUNCTIONS
#######################################################################


def get_color(color_key: str) -> str:
    """
    Get color value from design tokens.

    Args:
        color_key: Key from DESIGN_TOKENS['colors']

    Returns:
        Color value as string

    Example:
        >>> get_color('primary')
        '#0d6efd'
    """
    return DESIGN_TOKENS["colors"].get(color_key, DESIGN_TOKENS["colors"]["primary"])


def get_spacing(spacing_key: str) -> str:
    """
    Get spacing value from design tokens.

    Args:
        spacing_key: Key from DESIGN_TOKENS['spacing']

    Returns:
        Spacing value as string

    Example:
        >>> get_spacing('md')
        '1rem'
    """
    return DESIGN_TOKENS["spacing"].get(spacing_key, DESIGN_TOKENS["spacing"]["md"])


def get_card_style(variant: str = "default", elevated: bool = False) -> dict:
    """
    Get standardized card styling from design tokens.

    Args:
        variant: Color variant ('default', 'primary', 'success', etc.)
        elevated: Whether to use elevated shadow

    Returns:
        Dictionary of CSS style properties

    Example:
        >>> get_card_style('default', elevated=True)
        {'borderRadius': '0.375rem', 'boxShadow': '0 .5rem 1rem rgba(0,0,0,.15)', ...}
    """
    card_tokens = DESIGN_TOKENS["components"]["card"]
    layout_tokens = DESIGN_TOKENS["layout"]

    style = {
        "borderRadius": card_tokens["borderRadius"],
        "padding": card_tokens["padding"],
        "borderWidth": card_tokens["borderWidth"],
        "boxShadow": layout_tokens["shadow"]["md"]
        if elevated
        else layout_tokens["shadow"]["sm"],
    }

    # Add variant-specific styling
    if variant != "default":
        bg_color = (
            get_color(variant)
            if variant in DESIGN_TOKENS["colors"]
            else get_color("light")
        )
        style["backgroundColor"] = bg_color

    return style


def get_button_style(variant: str = "primary", size: str = "md") -> dict:
    """
    Get standardized button styling from design tokens.

    Args:
        variant: Button variant ('primary', 'secondary', 'success', etc.)
        size: Button size ('sm', 'md', 'lg')

    Returns:
        Dictionary of CSS style properties
    """
    button_tokens = DESIGN_TOKENS["components"]["button"]

    # Size adjustments
    size_map = {
        "sm": {"paddingY": "0.25rem", "paddingX": "0.5rem", "fontSize": "0.875rem"},
        "md": {
            "paddingY": button_tokens["paddingY"],
            "paddingX": button_tokens["paddingX"],
            "fontSize": button_tokens["fontSize"],
        },
        "lg": {"paddingY": "0.5rem", "paddingX": "1rem", "fontSize": "1.125rem"},
    }

    size_props = size_map.get(size, size_map["md"])

    return {
        "padding": f"{size_props['paddingY']} {size_props['paddingX']}",
        "fontSize": size_props["fontSize"],
        "borderRadius": button_tokens["borderRadius"],
        "minWidth": button_tokens["minWidth"],
        "minHeight": button_tokens["minHeight"],
    }


def get_responsive_cols(mobile: int = 12, tablet: int = 6, desktop: int = 4) -> dict:
    """
    Get responsive column configuration for Bootstrap grid.

    Args:
        mobile: Columns on mobile (<768px)
        tablet: Columns on tablet (768-992px)
        desktop: Columns on desktop (≥992px)

    Returns:
        Dictionary with xs, md, lg keys for dbc.Col

    Example:
        >>> get_responsive_cols(12, 6, 4)
        {'xs': 12, 'md': 6, 'lg': 4}
    """
    return {
        "xs": mobile,
        "md": tablet,
        "lg": desktop,
    }
