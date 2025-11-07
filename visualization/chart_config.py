"""Shared chart configuration utilities for consistent mobile-first design.

Provides standardized chart configurations that follow mobile-first principles
from the Copilot instructions for immediate value delivery.
"""

from typing import Dict, Any, List


def get_mobile_first_config() -> Dict[str, Any]:
    """Get mobile-first chart configuration for trend charts.

    Removes plotly tools and provides clean, immediate-value presentation.
    Follows mobile-first principles from Copilot instructions.
    AGGRESSIVELY removes all plotly toolbars for clean UX.

    Returns:
        Dictionary with plotly config options
    """
    return {
        "displayModeBar": False,  # CRITICAL: Completely remove plotly toolbar
        "staticPlot": False,  # Allow hover but no other interactions
        "responsive": True,  # Mobile-responsive scaling
        "toImageButtonOptions": {
            "format": "png",
            "filename": "chart",
            "height": 500,
            "width": 700,
            "scale": 1,
        },
        "displaylogo": False,  # Remove plotly logo
        "modeBarButtonsToRemove": [
            "zoom2d",
            "pan2d",
            "select2d",
            "lasso2d",
            "zoomIn2d",
            "zoomOut2d",
            "autoScale2d",
            "resetScale2d",
            "hoverClosestCartesian",
            "hoverCompareCartesian",
            "zoom3d",
            "pan3d",
            "resetCameraDefault3d",
            "resetCameraLastSave3d",
            "hoverClosest3d",
            "orbitRotation",
            "tableRotation",
            "zoomInGeo",
            "zoomOutGeo",
            "resetGeo",
            "hoverClosestGeo",
            "toImage",
            "sendDataToCloud",
            "hoverClosestGl2d",
            "hoverClosestPie",
            "toggleHover",
            "resetViews",
        ],
        "scrollZoom": False,  # Disable scroll zoom
        "doubleClick": False,  # Disable double-click interactions
        "showTips": False,  # Disable tips
        "showAxisDragHandles": False,  # Disable drag handles
        "showAxisRangeEntryBoxes": False,  # Disable range entry
        "editable": False,  # Make chart read-only
    }


def get_mobile_first_layout(
    title: str, height: int = 300, show_performance_zones: bool = False
) -> Dict[str, Any]:
    """Get mobile-first layout configuration for trend charts.

    Provides consistent layout that works well on mobile and desktop.
    ENSURES clean white background to match Work Distribution chart design.

    Args:
        title: Chart title
        height: Chart height in pixels
        show_performance_zones: Whether this chart should show DORA performance zones

    Returns:
        Dictionary with plotly layout options
    """
    return {
        "title": {"text": title, "x": 0.5, "xanchor": "center", "font": {"size": 14}},
        "height": height,
        "margin": dict(l=50, r=20, t=50, b=50),  # Mobile-friendly margins
        "plot_bgcolor": "white",  # CRITICAL: Clean white plot area
        "paper_bgcolor": "white",  # CRITICAL: Clean white outer background
        "hovermode": "x unified",
        "showlegend": False,  # Cleaner for trend charts
        "font": {"size": 12},
        "xaxis": {
            "showgrid": True,
            "gridwidth": 1,
            "gridcolor": "rgba(0,0,0,0.1)",  # Barely visible grid for consistency
            "tickfont": {"size": 10},
        },
        "yaxis": {
            "showgrid": True,
            "gridwidth": 1,
            "gridcolor": "rgba(0,0,0,0.1)",  # Barely visible grid for consistency
            "tickfont": {"size": 10},
        },
    }


def get_performance_zones(metric_name: str) -> List[Dict[str, Any]]:
    """Get DORA performance zones for specific metrics.

    Returns zone definitions for Elite/High/Medium/Low performance tiers.

    Args:
        metric_name: Name of the DORA metric

    Returns:
        List of zone dictionaries with y0, y1, color, and label
    """
    zones = {
        "deployment_frequency": [
            {
                "y0": 30,
                "y1": 1000,
                "color": "rgba(25, 135, 84, 0.1)",
                "label": "Elite (≥30/mo)",
            },
            {
                "y0": 7,
                "y1": 30,
                "color": "rgba(13, 110, 253, 0.1)",
                "label": "High (7-30/mo)",
            },
            {
                "y0": 1,
                "y1": 7,
                "color": "rgba(255, 193, 7, 0.1)",
                "label": "Medium (1-7/mo)",
            },
            {
                "y0": 0,
                "y1": 1,
                "color": "rgba(220, 53, 69, 0.1)",
                "label": "Low (<1/mo)",
            },
        ],
        "lead_time_for_changes": [
            {
                "y0": 0,
                "y1": 1,
                "color": "rgba(25, 135, 84, 0.1)",
                "label": "Elite (<1d)",
            },
            {
                "y0": 1,
                "y1": 7,
                "color": "rgba(13, 110, 253, 0.1)",
                "label": "High (1-7d)",
            },
            {
                "y0": 7,
                "y1": 30,
                "color": "rgba(255, 193, 7, 0.1)",
                "label": "Medium (1w-1mo)",
            },
            {
                "y0": 30,
                "y1": 365,
                "color": "rgba(220, 53, 69, 0.1)",
                "label": "Low (>1mo)",
            },
        ],
        "change_failure_rate": [
            {
                "y0": 0,
                "y1": 15,
                "color": "rgba(25, 135, 84, 0.1)",
                "label": "Elite (0-15%)",
            },
            {
                "y0": 15,
                "y1": 30,
                "color": "rgba(13, 110, 253, 0.1)",
                "label": "High (16-30%)",
            },
            {
                "y0": 30,
                "y1": 45,
                "color": "rgba(255, 193, 7, 0.1)",
                "label": "Medium (31-45%)",
            },
            {
                "y0": 45,
                "y1": 100,
                "color": "rgba(220, 53, 69, 0.1)",
                "label": "Low (>45%)",
            },
        ],
        "mttr": [
            {
                "y0": 0,
                "y1": 24,
                "color": "rgba(25, 135, 84, 0.1)",
                "label": "Elite (<1d)",
            },
            {
                "y0": 24,
                "y1": 168,
                "color": "rgba(13, 110, 253, 0.1)",
                "label": "High (1-7d)",
            },
            {
                "y0": 168,
                "y1": 720,
                "color": "rgba(255, 193, 7, 0.1)",
                "label": "Medium (1w-1mo)",
            },
            {
                "y0": 720,
                "y1": 8760,
                "color": "rgba(220, 53, 69, 0.1)",
                "label": "Low (>1mo)",
            },
        ],
    }

    return zones.get(metric_name, [])


def get_consistent_colors() -> Dict[str, str]:
    """Get consistent color scheme across all charts.

    Returns:
        Dictionary mapping metric names to colors
    """
    return {
        # DORA Metrics
        "deployment_frequency": "#0d6efd",  # Blue
        "lead_time_for_changes": "#198754",  # Green
        "change_failure_rate": "#dc3545",  # Red
        "mttr": "#fd7e14",  # Orange
        # Flow Metrics - using distinct colors based on metric meaning
        "flow_velocity": "#6f42c1",  # Purple
        "flow_time": "#6f42c1",  # Purple
        "flow_efficiency": "#198754",  # Green (higher is better - positive metric)
        "flow_load": "#6f42c1",  # Purple
        # Work Types
        "feature": "#198754",  # Green
        "defect": "#dc3545",  # Red
        "tech_debt": "#fd7e14",  # Orange
        "risk": "#ffc107",  # Yellow
    }
