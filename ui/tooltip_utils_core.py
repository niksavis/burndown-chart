"""
Tooltip Utilities Core Module

Core hoverlabel/template functions, performance utilities, and positioning
helpers for consistent tooltip styling across Plotly charts and Dash components.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
import time
from functools import lru_cache

# Application imports
from ui.style_constants import HOVER_MODES, TOOLTIP_STYLES, TYPOGRAPHY

#######################################################################
# TOOLTIP STYLING FUNCTIONS
#######################################################################


def get_tooltip_style(variant="default"):
    """
    Get tooltip styling configuration for a specific variant.

    Args:
        variant (str): Tooltip style variant
            (default, success, warning, error, info, primary, dark)

    Returns:
        dict: Style configuration for the tooltip
    """
    if variant in TOOLTIP_STYLES:
        return TOOLTIP_STYLES[variant]
    return TOOLTIP_STYLES["default"]


def create_hoverlabel_config(variant="default"):
    """
    Create a consistent hoverlabel configuration for Plotly charts.

    Args:
        variant (str): Tooltip style variant
            (default, success, warning, error, info, primary, dark)

    Returns:
        dict: hoverlabel configuration for Plotly
    """
    style = get_tooltip_style(variant)

    return {
        "bgcolor": style["bgcolor"],
        "bordercolor": style["bordercolor"],
        "font": {
            "family": TYPOGRAPHY["font_family"],
            "size": style["fontsize"],
            "color": style["fontcolor"],
        },
    }


def get_hover_mode(mode_key="standard"):
    """
    Get the appropriate hover mode setting for Plotly charts.

    Args:
        mode_key (str): Key for hover mode (standard, unified, compare, y_unified)

    Returns:
        str: Plotly hover mode setting
    """
    return HOVER_MODES.get(mode_key, HOVER_MODES["standard"])


def format_hover_template(
    title=None, fields=None, extra_info=None, include_extra_tag=True
):
    """
    Format a consistent hover template string for Plotly charts.

    This function formats hover templates for Plotly charts, properly handling
    Plotly's special syntax for format specifiers like %{y:.1f}.

    Args:
        title (str, optional): Title to display at the top of the tooltip
        fields (dict, optional): Dictionary of {label: value_template} pairs
        extra_info (str, optional): Additional information for the <extra> tag
        include_extra_tag (bool, optional): Whether to include the <extra> tag

    Returns:
        str: Formatted hover template string for Plotly
    """
    template = []

    # Add title if provided
    if title:
        template.append(f"<b>{title}</b><br>")

    # Add fields if provided
    if fields:
        for label, value in fields.items():
            # Don't process the value string, pass it directly to Plotly
            template.append(f"{label}: {value}<br>")

    # Join all template parts
    hover_text = "".join(template)

    # Add extra tag if requested
    if include_extra_tag:
        if extra_info:
            return f"{hover_text}<extra>{extra_info}</extra>"
        return f"{hover_text}<extra></extra>"

    return hover_text


def create_chart_layout_config(
    title=None, hover_mode="unified", tooltip_variant="dark"
):
    """
    Create a consistent chart layout configuration with tooltip settings.

    Args:
        title (str, optional): Chart title
        hover_mode (str): Hover mode setting (standard, unified, compare, y_unified)
        tooltip_variant (str): Tooltip style variant for the chart (default: "dark")

    Returns:
        dict: Layout configuration dictionary
    """
    config = {
        "hovermode": get_hover_mode(hover_mode),
        "hoverlabel": create_hoverlabel_config(tooltip_variant),
        "margin": {"l": 40, "r": 40, "t": 60, "b": 40},
    }

    if title:
        config["title"] = {
            "text": title,
            "font": {"family": TYPOGRAPHY["font_family"]},
        }

    return config


#######################################################################
# TOOLTIP PERFORMANCE UTILITIES
#######################################################################

# Global cache for frequently accessed tooltip content
_tooltip_cache = {}
_cache_timestamps = {}
_CACHE_TTL = 300  # 5 minutes cache TTL


@lru_cache(maxsize=128)
def get_cached_tooltip_style(variant="default"):
    """
    Get tooltip styling configuration with LRU caching for performance.

    Args:
        variant (str): Tooltip style variant

    Returns:
        dict: Cached style configuration
    """
    return get_tooltip_style(variant)


@lru_cache(maxsize=64)
def get_cached_hover_config(variant="default"):
    """
    Get cached hoverlabel configuration for Plotly charts.

    Args:
        variant (str): Tooltip style variant

    Returns:
        dict: Cached hoverlabel configuration
    """
    return create_hoverlabel_config(variant)


def cache_tooltip_content(key, content, ttl=None):
    """
    Cache tooltip content for reuse across components.

    Args:
        key (str): Cache key for the content
        content: Content to cache (string or Dash component)
        ttl (int): Time to live in seconds (default: 300)
    """
    ttl = ttl or _CACHE_TTL
    _tooltip_cache[key] = content
    _cache_timestamps[key] = time.time() + ttl


def get_cached_tooltip_content(key):
    """
    Retrieve cached tooltip content if available and not expired.

    Args:
        key (str): Cache key

    Returns:
        Content if cached and valid, None otherwise
    """
    if key not in _tooltip_cache:
        return None

    # Check if cache entry has expired
    if key in _cache_timestamps and time.time() > _cache_timestamps[key]:
        # Remove expired entry
        del _tooltip_cache[key]
        del _cache_timestamps[key]
        return None

    return _tooltip_cache[key]


def clear_tooltip_cache():
    """Clear all cached tooltip content."""
    _tooltip_cache.clear()
    _cache_timestamps.clear()


#######################################################################
# TOOLTIP POSITIONING UTILITIES
#######################################################################


def _is_mobile_context():
    """
    Determine if we're in a mobile context (placeholder for client-side logic).

    Note: This is a server-side approximation. In a real implementation,
    this would be enhanced with client-side device detection.

    Returns:
        bool: True if likely mobile context
    """
    # Server-side placeholder - in practice this could be enhanced with
    # user agent detection or client-side callbacks
    return False


def get_smart_placement(preferred="top", mobile_override=None):
    """
    Get smart tooltip placement that adapts to screen size.

    Args:
        preferred (str): Preferred placement (top, bottom, left, right)
        mobile_override (str): Override placement for mobile devices

    Returns:
        str: Optimal placement for the current context
    """
    # For mobile devices, prefer bottom placement to avoid viewport issues
    if mobile_override and _is_mobile_context():
        return mobile_override

    # Return preferred placement for desktop
    return preferred


def get_responsive_placement(element_position="center"):
    """
    Get responsive tooltip placement based on element position.

    Args:
        element_position (str): Position context (top, bottom, left, right, center)

    Returns:
        str: Recommended placement to avoid viewport edges
    """
    placement_map = {
        "top": "bottom",  # Elements at top show tooltip below
        "bottom": "top",  # Elements at bottom show tooltip above
        "left": "right",  # Elements at left show tooltip to right
        "right": "left",  # Elements at right show tooltip to left
        "center": "top",  # Center elements default to top
    }

    return placement_map.get(element_position, "top")


def create_adaptive_tooltip_config(base_delay=200, mobile_delay=300):
    """
    Create adaptive tooltip configuration that adjusts for device type.

    Args:
        base_delay (int): Base delay in milliseconds for desktop
        mobile_delay (int): Delay for mobile devices (usually longer)

    Returns:
        dict: Delay configuration
    """
    if _is_mobile_context():
        return {"show": mobile_delay, "hide": mobile_delay // 2}

    return {"show": base_delay, "hide": base_delay // 2}
