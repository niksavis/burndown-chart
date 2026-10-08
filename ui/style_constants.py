import re

from configuration.settings import COLOR_PALETTE

TYPOGRAPHY = {
    "font_family": "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
    "base_size": "1rem",
    "scale": {
        "h1": "2rem",
        "h2": "1.75rem",
        "h3": "1.5rem",
        "h4": "1.25rem",
        "h5": "1.1rem",
        "h6": "1rem",
        "small": "0.875rem",
        "xs": "0.75rem",
    },
    "weights": {"light": 300, "regular": 400, "medium": 500, "bold": 700},
}


PRIMARY_COLORS = {
    "primary": "rgb(13, 110, 253)",
    "teal": "rgb(32, 201, 151)",
    "orange": "rgb(253, 126, 20)",
    "purple": "rgb(102, 16, 242)",
    "pink": "rgb(214, 51, 132)",
    "indigo": "rgb(102, 16, 242)",
}

SEMANTIC_COLORS = {
    "primary": PRIMARY_COLORS["primary"],
    "success": "rgb(40, 167, 69)",
    "warning": "rgb(255, 193, 7)",
    "danger": "rgb(220, 53, 69)",
    "info": "rgb(13, 202, 240)",
    "secondary": "rgb(108, 117, 125)",
    "light": "rgb(248, 249, 250)",
    "dark": "rgb(33, 37, 41)",
}

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

CHART_COLORS = COLOR_PALETTE


def hex_to_rgb(hex_color):

    hex_color = hex_color.lstrip("#")
    red = int(hex_color[0:2], 16)
    green = int(hex_color[2:4], 16)
    blue = int(hex_color[4:6], 16)
    return f"rgb({red}, {green}, {blue})"


def rgb_to_rgba(rgb_color, alpha=1.0):

    if rgb_color.startswith("rgb("):
        rgb_part = rgb_color[4:-1]
        return f"rgba({rgb_part}, {alpha})"
    elif rgb_color.startswith("#"):
        return rgb_to_rgba(hex_to_rgb(rgb_color), alpha)
    return rgb_color


def parse_rgb_components(rgb_color):

    if not rgb_color.startswith("rgb"):
        if rgb_color.startswith("#"):
            rgb_color = hex_to_rgb(rgb_color)
        else:
            return (0, 0, 0)

    match = re.search(r"rgb a?\((\d+),\s*(\d+),\s*(\d+)", rgb_color)
    if match:
        return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    return (0, 0, 0)


def lighten_color(color, amount=0.1):

    r, g, b = parse_rgb_components(color)
    r = min(255, int(r + (255 - r) * amount))
    g = min(255, int(g + (255 - g) * amount))
    b = min(255, int(b + (255 - b) * amount))
    return f"rgb({r}, {g}, {b})"


def darken_color(color, amount=0.1):

    r, g, b = parse_rgb_components(color)
    r = max(0, int(r * (1 - amount)))
    g = max(0, int(g * (1 - amount)))
    b = max(0, int(b * (1 - amount)))
    return f"rgb({r}, {g}, {b})"


def get_color_variants(base_color):

    return {
        "base": base_color,
        "light": lighten_color(base_color, 0.15),
        "lighter": lighten_color(base_color, 0.3),
        "dark": darken_color(base_color, 0.15),
        "darker": darken_color(base_color, 0.3),
        "bg": rgb_to_rgba(base_color, 0.1),
        "border": rgb_to_rgba(base_color, 0.25),
        "focus": rgb_to_rgba(base_color, 0.25),
    }


def create_contrast_color(background_color):

    r, g, b = parse_rgb_components(background_color)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return NEUTRAL_COLORS["white"] if luminance < 0.5 else NEUTRAL_COLORS["black"]


TOOLTIP_STYLES = {
    "default": {
        "bgcolor": "rgba(33, 37, 41, 0.95)",
        "bordercolor": "rgba(255, 255, 255, 0.1)",
        "fontcolor": NEUTRAL_COLORS["gray-100"],
        "fontsize": 14,
    },
    "dark": {
        "bgcolor": "rgba(33, 37, 41, 0.95)",
        "bordercolor": "rgba(255, 255, 255, 0.1)",
        "fontcolor": NEUTRAL_COLORS["gray-100"],
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

HOVER_MODES = {
    "standard": "closest",
    "unified": "x unified",
    "compare": "x",
    "y_unified": "y unified",
}


METRIC_CARD = {
    "icon_size": "36px",
    "icon_circle_size": "36px",
    "icon_bg": "white",
    "padding": "0.75rem",
    "border_radius": "8px",
    "border_width": "1px",
    "margin_bottom": "0.5rem",
    "min_height": "120px",
}

METRIC_STATUS_COLORS = {
    "excellent": {
        "primary": "#28a745",
        "bg": "rgba(40, 167, 69, 0.1)",
        "border": "rgba(40, 167, 69, 0.2)",
        "icon": "fa-check-circle",
    },
    "good": {
        "primary": "#ffc107",
        "bg": "rgba(255, 193, 7, 0.1)",
        "border": "rgba(255, 193, 7, 0.2)",
        "icon": "fa-check-circle",
    },
    "warning": {
        "primary": "#fd7e14",
        "bg": "rgba(253, 126, 20, 0.1)",
        "border": "rgba(253, 126, 20, 0.2)",
        "icon": "fa-exclamation-triangle",
    },
    "danger": {
        "primary": "#dc3545",
        "bg": "rgba(220, 53, 69, 0.1)",
        "border": "rgba(220, 53, 69, 0.2)",
        "icon": "fa-exclamation-circle",
    },
    "info": {
        "primary": "#20c997",
        "bg": "rgba(32, 201, 151, 0.1)",
        "border": "rgba(32, 201, 151, 0.2)",
        "icon": "fa-info-circle",
    },
    "neutral": {
        "primary": "#6c757d",
        "bg": "rgba(108, 117, 125, 0.1)",
        "border": "rgba(108, 117, 125, 0.2)",
        "icon": "fa-equals",
    },
}

METRIC_CARD_BREAKPOINTS = {
    "mobile": 12,
    "tablet": 6,
    "desktop": 4,
    "wide": 3,
}


HELP_ICON = {
    "class": "fas fa-info-circle",
    "color": "#3b82f6",
    "size": "0.875rem",
    "margin_left": "0.5rem",
    "cursor": "pointer",
    "position": "inline",
}

HELP_ICON_POSITIONS = {
    "inline": {
        "class": "ms-1",
        "vertical_align": "middle",
    },
    "header": {
        "class": "ms-2",
        "vertical_align": "text-top",
    },
    "trailing": {
        "class": "ms-auto",
        "vertical_align": "middle",
    },
}


DESIGN_TOKENS = {
    "colors": {
        "primary": "#0d6efd",
        "secondary": "#6c757d",
        "success": "#198754",
        "warning": "#ffc107",
        "danger": "#dc3545",
        "info": "#0dcaf0",
        "light": "#f8f9fa",
        "dark": "#343a40",
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
        "primary-hover": "#0b5ed7",
        "primary-active": "#0a58ca",
        "focus-shadow": "rgba(13, 110, 253, 0.25)",
        "teal": "#20c997",
        "orange": "#fd7e14",
        "purple": "#6610f2",
        "pink": "#d63384",
        "indigo": "#6610f2",
        "cyan": "#0dcaf0",
    },
    "spacing": {
        "xs": "0.25rem",
        "sm": "0.5rem",
        "md": "1rem",
        "lg": "1.5rem",
        "xl": "2rem",
        "xxl": "3rem",
        "xxxl": "4rem",
    },
    "typography": {
        "fontFamily": "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
        "size": {
            "xs": "0.75rem",
            "sm": "0.875rem",
            "base": "1rem",
            "lg": "1.125rem",
            "xl": "1.25rem",
            "2xl": "1.5rem",
            "3xl": "1.875rem",
            "4xl": "2.25rem",
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
    "layout": {
        "borderRadius": {
            "sm": "0.25rem",
            "md": "0.375rem",
            "lg": "0.5rem",
            "xl": "0.75rem",
            "full": "9999px",
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
    "breakpoints": {
        "xs": "0px",
        "sm": "576px",
        "md": "768px",
        "lg": "992px",
        "xl": "1200px",
        "xxl": "1400px",
    },
    "components": {
        "button": {
            "paddingY": "0.375rem",
            "paddingX": "0.75rem",
            "fontSize": "1rem",
            "borderRadius": "0.375rem",
            "minWidth": "44px",
            "minHeight": "44px",
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
            "minHeight": "44px",
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
    "mobile": {
        "touchTargetMin": "44px",
        "bottomSheetMaxHeight": "80vh",
        "navBarHeight": "56px",
        "fabSize": "56px",
        "fabPosition": "16px",
        "swipeThreshold": "50px",
    },
}


def get_color(color_key: str) -> str:

    return DESIGN_TOKENS["colors"].get(color_key, DESIGN_TOKENS["colors"]["primary"])


def get_spacing(spacing_key: str) -> str:

    return DESIGN_TOKENS["spacing"].get(spacing_key, DESIGN_TOKENS["spacing"]["md"])


def get_card_style(variant: str = "default", elevated: bool = False) -> dict:

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

    if variant != "default":
        bg_color = (
            get_color(variant)
            if variant in DESIGN_TOKENS["colors"]
            else get_color("light")
        )
        style["backgroundColor"] = bg_color

    return style


def get_button_style(variant: str = "primary", size: str = "md") -> dict:

    button_tokens = DESIGN_TOKENS["components"]["button"]

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

    return {
        "xs": mobile,
        "md": tablet,
        "lg": desktop,
    }
