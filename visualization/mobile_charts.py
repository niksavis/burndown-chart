"""
Mobile Chart Configuration Module

This module provides mobile-optimized chart configurations and utilities
for responsive data visualization on mobile devices.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
from typing import Dict, Any

# Third-party library imports


def get_mobile_chart_config(viewport_size: str = "mobile") -> Dict[str, Any]:
    """
    Get mobile-optimized chart configuration.
    
    Args:
        viewport_size: "mobile", "tablet", or "desktop"
        
    Returns:
        Dictionary with mobile-optimized chart configuration
    """
    # Base configuration for all devices
    base_config = {
        "displayModeBar": viewport_size != "mobile",  # Hide toolbar on mobile
        "responsive": True,
        "scrollZoom": True,  # Enable mobile-friendly zooming
        "doubleClick": "reset+autosize",
        "showTips": True,
        "displaylogo": False,
    }
    
    if viewport_size == "mobile":
        # Mobile-specific configuration
        mobile_config = {
            **base_config,
            "modeBarButtonsToRemove": [
                "pan2d", "select2d", "lasso2d", "resetScale2d", 
                "zoomIn2d", "zoomOut2d", "autoScale2d", "hoverClosestCartesian", 
                "hoverCompareCartesian", "toggleSpikelines"
            ],
            "toImageButtonOptions": {
                "format": "png",
                "filename": "burndown_chart",
                "height": 400,  # Smaller export size for mobile
                "width": 600,   # Smaller export size for mobile
                "scale": 2
            }
        }
        return mobile_config
    elif viewport_size == "tablet":
        # Tablet-specific configuration
        tablet_config = {
            **base_config,
            "modeBarButtonsToRemove": [
                "select2d", "lasso2d", "hoverClosestCartesian", 
                "hoverCompareCartesian"
            ],
        }
        return tablet_config
    else:
        # Desktop configuration (full features)
        return base_config


def get_mobile_chart_layout(viewport_size: str = "mobile") -> Dict[str, Any]:
    """
    Get mobile-optimized chart layout configuration.
    
    Args:
        viewport_size: "mobile", "tablet", or "desktop"
        
    Returns:
        Dictionary with mobile-optimized layout configuration
    """
    if viewport_size == "mobile":
        return {
            "font": {"size": 11, "family": "system-ui, -apple-system, sans-serif"},
            "margin": {"t": 30, "r": 15, "b": 50, "l": 50},  # Tighter margins for mobile
            "height": 400,  # Shorter height for mobile screens
            "legend": {
                "orientation": "h",
                "yanchor": "bottom", 
                "y": -0.15,  # Position legend below chart
                "xanchor": "center", 
                "x": 0.5,
                "font": {"size": 10}
            },
            "xaxis": {
                "title": {"font": {"size": 10}},
                "tickfont": {"size": 9},
                "tickangle": -45  # Rotate dates for better mobile fit
            },
            "yaxis": {
                "title": {"font": {"size": 10}},
                "tickfont": {"size": 9}
            },
            "yaxis2": {
                "title": {"font": {"size": 10}},
                "tickfont": {"size": 9}
            }
        }
    elif viewport_size == "tablet":
        return {
            "font": {"size": 12, "family": "system-ui, -apple-system, sans-serif"},
            "margin": {"t": 50, "r": 30, "b": 60, "l": 60},
            "height": 500,
            "legend": {
                "orientation": "h",
                "yanchor": "bottom", 
                "y": 1.02,
                "xanchor": "center", 
                "x": 0.5
            }
        }
    else:
        # Desktop layout (existing default)
        return {
            "font": {"size": 14, "family": "system-ui, -apple-system, sans-serif"},
            "margin": {"t": 80, "r": 60, "b": 50, "l": 60},
            "height": 700,
            "legend": {
                "orientation": "h",
                "yanchor": "bottom", 
                "y": 1.02,
                "xanchor": "center", 
                "x": 0.5
            }
        }


def get_mobile_hover_template(chart_type: str = "burndown") -> str:
    """
    Get mobile-optimized hover template for charts.
    
    Args:
        chart_type: Type of chart ("burndown", "items", "points", "scope")
        
    Returns:
        HTML string for hover template optimized for mobile
    """
    # Shorter, more concise hover templates for mobile
    templates = {
        "burndown": (
            "<b>%{x}</b><br>"
            "Items: %{y}<br>"
            "<extra></extra>"
        ),
        "items": (
            "<b>%{x}</b><br>"
            "Completed: %{y}<br>"
            "<extra></extra>"
        ),
        "points": (
            "<b>%{x}</b><br>"
            "Points: %{y}<br>"
            "<extra></extra>"
        ),
        "scope": (
            "<b>%{x}</b><br>"
            "Scope: %{y}<br>"
            "<extra></extra>"
        )
    }
    
    return templates.get(chart_type, templates["burndown"])


def apply_mobile_chart_optimizations(fig, viewport_size: str = "mobile", chart_type: str = "burndown"):
    """
    Apply mobile optimizations to an existing Plotly figure.
    
    Args:
        fig: Plotly figure object
        viewport_size: "mobile", "tablet", or "desktop"
        chart_type: Type of chart for hover template optimization
        
    Returns:
        Optimized Plotly figure
    """
    # Get mobile layout
    mobile_layout = get_mobile_chart_layout(viewport_size)
    
    # Apply mobile layout
    fig.update_layout(**mobile_layout)
    
    # Apply mobile-specific trace optimizations
    if viewport_size == "mobile":
        # Optimize line widths for mobile
        fig.update_traces(
            line_width=2,  # Slightly thicker lines for mobile visibility
            marker_size=6,  # Larger markers for touch interaction
        )
        
        # Update hover templates for mobile
        mobile_template = get_mobile_hover_template(chart_type)
        fig.update_traces(hovertemplate=mobile_template)
        
        # Optimize annotations for mobile
        fig.update_annotations(
            font_size=9,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="rgba(0,0,0,0.1)",
            borderwidth=1
        )
    
    return fig


def create_mobile_optimized_chart(figure_data: Dict, viewport_size: str = "mobile", chart_type: str = "burndown"):
    """
    Create a mobile-optimized chart component.
    
    Args:
        figure_data: Plotly figure data dictionary
        viewport_size: "mobile", "tablet", or "desktop"
        chart_type: Type of chart for optimization
        
    Returns:
        Optimized figure data dictionary
    """
    # Apply mobile optimizations to the figure
    if hasattr(figure_data, 'update_layout'):
        # It's a figure object
        optimized_fig = apply_mobile_chart_optimizations(figure_data, viewport_size, chart_type)
        return optimized_fig
    else:
        # It's figure data dictionary
        return figure_data  # Return as-is if not a figure object
