"""
Style Constants Module

This module contains constants used across different UI modules.
Separating these constants helps prevent circular imports between modules.
"""

#######################################################################
# IMPORTS
#######################################################################

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

# Extended semantic color mappings
SEMANTIC_COLORS = {
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

#######################################################################
# TOOLTIP CONSTANTS
#######################################################################

# Tooltip styles configuration
TOOLTIP_STYLES = {
    "default": {
        "bgcolor": "rgba(255, 255, 255, 0.95)",
        "bordercolor": "rgba(200, 200, 200, 0.8)",
        "fontcolor": "#343a40",  # gray-800
        "fontsize": 14,
    },
    "success": {
        "bgcolor": "rgba(240, 255, 240, 0.95)",
        "bordercolor": "rgb(40, 167, 69)",  # success color
        "fontcolor": "#343a40",  # gray-800
        "fontsize": 14,
    },
    "warning": {
        "bgcolor": "rgba(255, 252, 235, 0.95)",
        "bordercolor": "rgb(255, 193, 7)",  # warning color
        "fontcolor": "#343a40",  # gray-800
        "fontsize": 14,
    },
    "error": {
        "bgcolor": "rgba(255, 235, 235, 0.95)",
        "bordercolor": "rgb(220, 53, 69)",  # danger color
        "fontcolor": "#343a40",  # gray-800
        "fontsize": 14,
    },
    "info": {
        "bgcolor": "rgba(235, 250, 255, 0.95)",
        "bordercolor": "rgb(13, 202, 240)",  # info color
        "fontcolor": "#343a40",  # gray-800
        "fontsize": 14,
    },
    "primary": {
        "bgcolor": "rgba(235, 245, 255, 0.95)",
        "bordercolor": "rgb(13, 110, 253)",  # primary blue
        "fontcolor": "#343a40",  # gray-800
        "fontsize": 14,
    },
    "dark": {
        "bgcolor": "rgba(33, 37, 41, 0.95)",  # dark background
        "bordercolor": "rgba(100, 100, 100, 0.8)",
        "fontcolor": "#f8f9fa",  # light text
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
