"""
Unified Chart Configuration Module

This module provides standardized chart configurations for all Plotly charts
across the application, ensuring visual consistency and optimal user experience.

Design Philosophy:
- Mobile-first responsive design
- Consistent toolbar behavior across all charts
- Accessible and user-friendly interactions
- Professional, cohesive appearance
"""

from typing import Dict, Any, Optional


#######################################################################
# CHART DISPLAY CONFIGURATION
#######################################################################


def get_chart_config(
    responsive: bool = True,
    display_mode_bar: Optional[bool] = None,
    display_logo: bool = False,
    mobile_friendly: bool = True,
    **kwargs,
) -> Dict[str, Any]:
    """
    Get standardized chart configuration for Plotly figures.

    This ensures all charts across the app have consistent behavior:
    - Toolbar visibility (displayModeBar)
    - Responsive sizing
    - Download options
    - Interaction modes

    Args:
        responsive: Enable responsive chart sizing (default: True)
        display_mode_bar: Show Plotly toolbar. If None, auto-detects based on
                         mobile_friendly setting (default: None)
        display_logo: Show Plotly logo in toolbar (default: False)
        mobile_friendly: Optimize for mobile devices (default: True)
        **kwargs: Additional config options to override defaults

    Returns:
        Dict containing Plotly config options

    Examples:
        >>> # Standard desktop chart
        >>> config = get_chart_config()

        >>> # Force toolbar visibility
        >>> config = get_chart_config(display_mode_bar=True)

        >>> # Custom config with overrides
        >>> config = get_chart_config(scrollZoom=True, doubleClick='reset')
    """
    # Auto-detect displayModeBar based on mobile_friendly if not explicitly set
    if display_mode_bar is None:
        display_mode_bar = True  # Show toolbar by default on all devices

    # Base configuration - consistent across all charts
    config = {
        "responsive": responsive,
        "displayModeBar": display_mode_bar,
        "displaylogo": display_logo,
        "modeBarButtonsToRemove": [
            "lasso2d",  # Remove lasso select (rarely used)
            "select2d",  # Remove box select (rarely used)
            "toggleSpikelines",  # Remove spike lines toggle
        ],
        "toImageButtonOptions": {
            "format": "png",
            "filename": "chart",
            "height": None,  # Use current chart height
            "width": None,  # Use current chart width
            "scale": 2,  # High-resolution export (2x)
        },
        # Enable useful interactions
        "scrollZoom": False,  # Disable scroll zoom to prevent accidental zooming
        "doubleClick": "reset+autosize",  # Double-click resets view and autosizes
    }

    # Apply mobile optimizations if requested
    if mobile_friendly:
        config.update(
            {
                "modeBarButtonsToAdd": [],  # Can add mobile-specific buttons if needed
            }
        )

    # Override with any custom kwargs
    config.update(kwargs)

    return config


def get_chart_layout_config(
    height: Optional[int] = None,
    margin: Optional[Dict[str, int]] = None,
    font_size: int = 12,
    show_legend: bool = True,
    legend_position: str = "top",
    mobile_optimized: bool = True,
    **kwargs,
) -> Dict[str, Any]:
    """
    Get standardized chart layout configuration.

    This ensures consistent spacing, fonts, and visual styling across all charts.

    Args:
        height: Chart height in pixels (default: None, auto-sized)
        margin: Custom margins dict with t, r, b, l keys (default: None, uses standards)
        font_size: Base font size for chart text (default: 12)
        show_legend: Display chart legend (default: True)
        legend_position: Legend position - 'top', 'bottom', 'left', 'right' (default: 'top')
        mobile_optimized: Apply mobile-friendly spacing (default: True)
        **kwargs: Additional layout options to override defaults

    Returns:
        Dict containing Plotly layout options

    Examples:
        >>> # Standard layout
        >>> layout = get_chart_layout_config()

        >>> # Custom height and margins
        >>> layout = get_chart_layout_config(height=600, margin={"t": 50, "b": 50})

        >>> # Hide legend for cleaner mobile view
        >>> layout = get_chart_layout_config(show_legend=False)
    """
    # Standard margins - tighter on mobile
    if margin is None:
        if mobile_optimized:
            margin = {"t": 40, "r": 20, "b": 50, "l": 60}
        else:
            margin = {"t": 60, "r": 40, "b": 60, "l": 80}

    # Legend positioning
    legend_configs = {
        "top": {
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
        "bottom": {
            "orientation": "h",
            "yanchor": "top",
            "y": -0.2,
            "xanchor": "center",
            "x": 0.5,
        },
        "left": {
            "orientation": "v",
            "yanchor": "top",
            "y": 1,
            "xanchor": "right",
            "x": -0.05,
        },
        "right": {
            "orientation": "v",
            "yanchor": "top",
            "y": 1,
            "xanchor": "left",
            "x": 1.02,
        },
    }

    legend_config = legend_configs.get(legend_position, legend_configs["top"])

    # Base layout configuration
    layout = {
        "font": {
            "size": font_size,
            "family": "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
        },
        "margin": margin,
        "showlegend": show_legend,
        "legend": legend_config if show_legend else {},
        "hovermode": "closest",
        "paper_bgcolor": "white",
        "plot_bgcolor": "rgba(0,0,0,0.02)",
        "xaxis": {
            "showgrid": True,
            "gridcolor": "rgba(0,0,0,0.1)",
            "zeroline": False,
        },
        "yaxis": {
            "showgrid": True,
            "gridcolor": "rgba(0,0,0,0.1)",
            "zeroline": False,
        },
    }

    # Add height if specified
    if height is not None:
        layout["height"] = height

    # Override with any custom kwargs
    layout.update(kwargs)

    return layout


#######################################################################
# PRESET CONFIGURATIONS
#######################################################################


def get_burndown_chart_config() -> Dict[str, Any]:
    """Get preset config for burndown/burnup charts."""
    return get_chart_config(
        display_mode_bar=True,
        modeBarButtonsToRemove=[
            "lasso2d",
            "select2d",
            "toggleSpikelines",
        ],
    )


def get_weekly_chart_config() -> Dict[str, Any]:
    """Get preset config for weekly items/points bar charts."""
    return get_chart_config(
        display_mode_bar=True,
        modeBarButtonsToRemove=[
            "lasso2d",
            "select2d",
            "toggleSpikelines",
        ],
    )


def get_scope_metrics_chart_config() -> Dict[str, Any]:
    """Get preset config for scope metrics indicator charts."""
    return get_chart_config(
        display_mode_bar=True,
        modeBarButtonsToRemove=[
            "lasso2d",
            "select2d",
            "toggleSpikelines",
        ],
    )


def get_bug_analysis_chart_config() -> Dict[str, Any]:
    """Get preset config for bug analysis charts."""
    return get_chart_config(
        display_mode_bar=True,
        modeBarButtonsToRemove=[
            "lasso2d",
            "select2d",
            "toggleSpikelines",
        ],
    )


#######################################################################
# MOBILE DETECTION UTILITIES
#######################################################################


def is_mobile_viewport(width: Optional[int] = None) -> bool:
    """
    Determine if viewport is mobile-sized.

    Args:
        width: Viewport width in pixels (default: None, assumes mobile threshold)

    Returns:
        bool: True if mobile viewport, False otherwise

    Note:
        Bootstrap md breakpoint is 768px - we use this as our mobile threshold.
    """
    MOBILE_BREAKPOINT = 768

    if width is None:
        return False  # Default to desktop if width unknown

    return width < MOBILE_BREAKPOINT
