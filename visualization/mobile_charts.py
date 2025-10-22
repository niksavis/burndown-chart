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
import plotly.graph_objects as go


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
                "pan2d",
                "select2d",
                "lasso2d",
                "resetScale2d",
                "zoomIn2d",
                "zoomOut2d",
                "autoScale2d",
                "hoverClosestCartesian",
                "hoverCompareCartesian",
                "toggleSpikelines",
            ],
            "toImageButtonOptions": {
                "format": "png",
                "filename": "burndown_chart",
                "height": 400,  # Smaller export size for mobile
                "width": 600,  # Smaller export size for mobile
                "scale": 2,
            },
        }
        return mobile_config
    elif viewport_size == "tablet":
        # Tablet-specific configuration
        tablet_config = {
            **base_config,
            "modeBarButtonsToRemove": [
                "select2d",
                "lasso2d",
                "hoverClosestCartesian",
                "hoverCompareCartesian",
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
            "margin": {
                "t": 30,
                "r": 15,
                "b": 50,
                "l": 50,
            },  # Tighter margins for mobile
            "height": 400,  # Shorter height for mobile screens
            "legend": {
                "orientation": "h",
                "yanchor": "bottom",
                "y": -0.15,  # Position legend below chart
                "xanchor": "center",
                "x": 0.5,
                "font": {"size": 10},
            },
            "xaxis": {
                "title": {"font": {"size": 10}},
                "tickfont": {"size": 9},
                "tickangle": -45,  # Rotate dates for better mobile fit
            },
            "yaxis": {"title": {"font": {"size": 10}}, "tickfont": {"size": 9}},
            "yaxis2": {"title": {"font": {"size": 10}}, "tickfont": {"size": 9}},
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
                "x": 0.5,
            },
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
                "x": 0.5,
            },
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
        "burndown": ("<b>%{x}</b><br>Items: %{y}<br><extra></extra>"),
        "items": ("<b>%{x}</b><br>Completed: %{y}<br><extra></extra>"),
        "points": ("<b>%{x}</b><br>Points: %{y}<br><extra></extra>"),
        "scope": ("<b>%{x}</b><br>Scope: %{y}<br><extra></extra>"),
    }

    return templates.get(chart_type, templates["burndown"])


def apply_mobile_chart_optimizations(
    fig, viewport_size: str = "mobile", chart_type: str = "burndown"
):
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
            borderwidth=1,
        )

    return fig


def create_mobile_optimized_chart(
    figure_data: Dict, viewport_size: str = "mobile", chart_type: str = "burndown"
):
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
    if hasattr(figure_data, "update_layout"):
        # It's a figure object
        optimized_fig = apply_mobile_chart_optimizations(
            figure_data, viewport_size, chart_type
        )
        return optimized_fig
    else:
        # It's figure data dictionary
        return figure_data  # Return as-is if not a figure object


def create_bug_trend_chart(
    weekly_stats: list[Dict], viewport_size: str = "mobile"
) -> go.Figure:
    """
    Create bug trend chart showing bugs created vs resolved per week.

    Implements T037 - Bug trend visualization with mobile optimization.
    Implements T037a - Visual warnings for 3+ consecutive weeks of negative trends.

    Args:
        weekly_stats: List of weekly bug statistics from calculate_bug_statistics()
        viewport_size: "mobile", "tablet", or "desktop"

    Returns:
        Plotly Figure object with bug trend visualization
    """
    import plotly.graph_objects as go

    if not weekly_stats:
        # Return empty chart with message
        fig = go.Figure()
        fig.add_annotation(
            text="No bug data available for the selected period",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14, color="gray"),
        )
        fig.update_layout(
            title="Bug Trends: Creation vs Resolution",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
        )
        return fig

    # Extract data for plotting
    weeks = [stat["week"] for stat in weekly_stats]
    bugs_created = [stat["bugs_created"] for stat in weekly_stats]
    bugs_resolved = [stat["bugs_resolved"] for stat in weekly_stats]

    # Create figure with two traces
    fig = go.Figure()

    # Bugs created line (red/orange color)
    fig.add_trace(
        go.Scatter(
            x=weeks,
            y=bugs_created,
            name="Bugs Created",
            mode="lines+markers",
            line=dict(color="#dc3545", width=2),  # Red color
            marker=dict(size=6),
            hovertemplate="<b>%{x}</b><br>Created: %{y}<extra></extra>",
        )
    )

    # Bugs resolved line (green color)
    fig.add_trace(
        go.Scatter(
            x=weeks,
            y=bugs_resolved,
            name="Bugs Closed",
            mode="lines+markers",
            line=dict(color="#28a745", width=2),  # Green color
            marker=dict(size=6),
            hovertemplate="<b>%{x}</b><br>Closed: %{y}<extra></extra>",
        )
    )

    # T037a: Add visual warnings for 3+ consecutive weeks where creation > closure
    warning_shapes = []
    consecutive_negative_weeks = 0
    warning_start_idx = None

    for idx, stat in enumerate(weekly_stats):
        if stat["bugs_created"] > stat["bugs_resolved"]:
            consecutive_negative_weeks += 1
            if consecutive_negative_weeks == 1:
                warning_start_idx = idx
        else:
            # Check if we had 3+ consecutive negative weeks
            if consecutive_negative_weeks >= 3 and warning_start_idx is not None:
                # Add background highlight for warning period
                warning_shapes.append(
                    dict(
                        type="rect",
                        xref="x",
                        yref="paper",
                        x0=weeks[warning_start_idx],
                        x1=weeks[idx - 1],
                        y0=0,
                        y1=1,
                        fillcolor="rgba(220, 53, 69, 0.15)",  # Light red
                        layer="below",
                        line_width=0,
                    )
                )
            consecutive_negative_weeks = 0
            warning_start_idx = None

    # Check final period if it ends with warnings
    if consecutive_negative_weeks >= 3 and warning_start_idx is not None:
        warning_shapes.append(
            dict(
                type="rect",
                xref="x",
                yref="paper",
                x0=weeks[warning_start_idx],
                x1=weeks[-1],
                y0=0,
                y1=1,
                fillcolor="rgba(220, 53, 69, 0.15)",  # Light red
                layer="below",
                line_width=0,
            )
        )

    # Configure layout
    layout_config = get_mobile_chart_layout(viewport_size)

    # Remove xaxis/yaxis from layout_config to avoid conflicts (we'll set them explicitly)
    layout_config_clean = {
        k: v for k, v in layout_config.items() if k not in ["xaxis", "yaxis", "yaxis2"]
    }

    fig.update_layout(
        title="Bug Trends: Creation vs Resolution",
        xaxis=dict(
            title="Week",
            tickangle=-45 if viewport_size == "mobile" else 0,
            tickfont=dict(size=10 if viewport_size == "mobile" else 12),
        ),
        yaxis=dict(
            title="Bug Count",
            tickfont=dict(size=10 if viewport_size == "mobile" else 12),
        ),
        shapes=warning_shapes,  # Add warning highlights
        hovermode="x unified",
        **layout_config_clean,
    )

    # Add legend configuration
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h" if viewport_size == "mobile" else "v",
            yanchor="bottom",
            y=-0.3 if viewport_size == "mobile" else 1.0,
            xanchor="left" if viewport_size == "mobile" else "left",
            x=0 if viewport_size == "mobile" else 1.02,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="rgba(0,0,0,0.1)",
            borderwidth=1,
        ),
    )

    return fig
