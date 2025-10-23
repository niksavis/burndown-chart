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
        "displayModeBar": True,  # Always show toolbar for download PNG capability
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
    weekly_stats: list[Dict],
    viewport_size: str = "mobile",
    include_forecast: bool = True,
) -> go.Figure:
    """
    Create bug trend chart showing bugs created vs resolved per week with next week forecast.

    Implements T037 - Bug trend visualization with mobile optimization.
    Implements T037a - Visual warnings for 3+ consecutive weeks of negative trends.

    Args:
        weekly_stats: List of weekly bug statistics from calculate_bug_statistics()
        viewport_size: "mobile", "tablet", or "desktop"
        include_forecast: Whether to include next week forecast (default: True)

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

    # Add next week forecast if requested and have enough data
    if include_forecast and len(weekly_stats) >= 2:
        from data.bug_processing import generate_bug_weekly_forecast

        forecast = generate_bug_weekly_forecast(weekly_stats)

        if not forecast.get("insufficient_data", False):
            next_week = forecast["created"]["next_week"]

            # Created forecast with error bars
            created_ml = forecast["created"]["most_likely"]
            created_upper = forecast["created"]["optimistic"] - created_ml
            created_lower = created_ml - forecast["created"]["pessimistic"]

            created_range_text = f"{forecast['created']['pessimistic']:.1f}-{forecast['created']['optimistic']:.1f}"
            fig.add_trace(
                go.Scatter(
                    x=[next_week],
                    y=[created_ml],
                    name="Created Forecast",
                    mode="markers",
                    marker=dict(
                        size=10,
                        color="#dc3545",
                        symbol="x",
                        line=dict(width=2, color="white"),
                    ),
                    error_y=dict(
                        type="data",
                        symmetric=False,
                        array=[created_upper],
                        arrayminus=[created_lower],
                        color="rgba(220, 53, 69, 0.4)",
                        thickness=2,
                    ),
                    hovertemplate=f"<b>%{{x}}</b><br>Forecast Created: %{{y:.1f}}<br>Range: {created_range_text}<extra></extra>",
                )
            )

            # Resolved forecast with error bars
            resolved_ml = forecast["resolved"]["most_likely"]
            resolved_upper = forecast["resolved"]["optimistic"] - resolved_ml
            resolved_lower = resolved_ml - forecast["resolved"]["pessimistic"]

            resolved_range_text = f"{forecast['resolved']['pessimistic']:.1f}-{forecast['resolved']['optimistic']:.1f}"
            fig.add_trace(
                go.Scatter(
                    x=[next_week],
                    y=[resolved_ml],
                    name="Resolved Forecast",
                    mode="markers",
                    marker=dict(
                        size=10,
                        color="#28a745",
                        symbol="x",
                        line=dict(width=2, color="white"),
                    ),
                    error_y=dict(
                        type="data",
                        symmetric=False,
                        array=[resolved_upper],
                        arrayminus=[resolved_lower],
                        color="rgba(40, 167, 69, 0.4)",
                        thickness=2,
                    ),
                    hovertemplate=f"<b>%{{x}}</b><br>Forecast Resolved: %{{y:.1f}}<br>Range: {resolved_range_text}<extra></extra>",
                )
            )

            # Add vertical line between historical and forecast
            # Position annotation away from toolbar to avoid overlap
            fig.add_vline(
                x=len(weeks) - 0.5,
                line_dash="dash",
                line_color="rgba(0, 0, 0, 0.3)",
            )

            # Add annotation separately for better positioning control
            fig.add_annotation(
                x=len(weeks) - 0.5,
                y=1.02,
                xref="x",
                yref="paper",
                text="Forecast",
                showarrow=False,
                font=dict(size=11, color="rgba(0, 0, 0, 0.6)"),
                xanchor="center",
                yanchor="bottom",
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


def create_bug_investment_chart(
    weekly_stats: list[Dict],
    viewport_size: str = "mobile",
    include_forecast: bool = True,
) -> go.Figure:
    """
    Create bug investment chart showing bug items and story points per week with next week forecast.

    Implements T052 - Bug investment visualization with dual-axis (items + story points).

    Args:
        weekly_stats: List of weekly bug statistics from calculate_bug_statistics()
        viewport_size: "mobile", "tablet", or "desktop"
        include_forecast: Whether to include next week forecast (default: True)

    Returns:
        Plotly Figure object with dual-axis bug investment visualization
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

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
            title="Bug Investment: Items vs Story Points",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
        )
        return fig

    # Extract data for plotting
    weeks = [stat["week"] for stat in weekly_stats]
    bugs_created = [stat["bugs_created"] for stat in weekly_stats]
    bugs_resolved = [stat["bugs_resolved"] for stat in weekly_stats]
    points_created = [stat["bugs_points_created"] for stat in weekly_stats]
    points_resolved = [stat["bugs_points_resolved"] for stat in weekly_stats]

    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Bug items traces (primary y-axis)
    fig.add_trace(
        go.Bar(
            x=weeks,
            y=bugs_created,
            name="Items Created",
            marker=dict(color="#dc3545", opacity=0.7),  # Red
            hovertemplate="<b>%{x}</b><br>Items Created: %{y}<extra></extra>",
            yaxis="y",
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Bar(
            x=weeks,
            y=bugs_resolved,
            name="Items Resolved",
            marker=dict(color="#28a745", opacity=0.7),  # Green
            hovertemplate="<b>%{x}</b><br>Items Resolved: %{y}<extra></extra>",
            yaxis="y",
        ),
        secondary_y=False,
    )

    # Story points traces (secondary y-axis)
    fig.add_trace(
        go.Scatter(
            x=weeks,
            y=points_created,
            name="Points Created",
            mode="lines+markers",
            line=dict(color="#ff8c00", width=2, dash="dot"),  # Dark orange
            marker=dict(size=6, symbol="diamond"),
            hovertemplate="<b>%{x}</b><br>Points Created: %{y}<extra></extra>",
            yaxis="y2",
        ),
        secondary_y=True,
    )

    fig.add_trace(
        go.Scatter(
            x=weeks,
            y=points_resolved,
            name="Points Resolved",
            mode="lines+markers",
            line=dict(color="#20c997", width=2, dash="dot"),  # Teal/green
            marker=dict(size=6, symbol="diamond"),
            hovertemplate="<b>%{x}</b><br>Points Resolved: %{y}<extra></extra>",
            yaxis="y2",
        ),
        secondary_y=True,
    )

    # Add next week forecast if requested and have enough data
    if include_forecast and len(weekly_stats) >= 2:
        from data.bug_processing import generate_bug_weekly_forecast

        forecast = generate_bug_weekly_forecast(weekly_stats)

        if not forecast.get("insufficient_data", False):
            next_week = forecast["created"]["next_week"]

            # Forecast for items created/resolved (bars with pattern)
            created_ml = forecast["created"]["most_likely"]
            resolved_ml = forecast["resolved"]["most_likely"]

            fig.add_trace(
                go.Bar(
                    x=[next_week],
                    y=[created_ml],
                    name="Items Forecast (Created)",
                    marker=dict(
                        color="#dc3545",
                        opacity=0.5,
                        pattern_shape="x",  # Pattern to distinguish forecast
                    ),
                    hovertemplate="<b>%{x}</b><br>Forecast Created: %{y:.1f}<extra></extra>",
                    yaxis="y",
                ),
                secondary_y=False,
            )

            fig.add_trace(
                go.Bar(
                    x=[next_week],
                    y=[resolved_ml],
                    name="Items Forecast (Resolved)",
                    marker=dict(
                        color="#28a745",
                        opacity=0.5,
                        pattern_shape="x",
                    ),
                    hovertemplate="<b>%{x}</b><br>Forecast Resolved: %{y:.1f}<extra></extra>",
                    yaxis="y",
                ),
                secondary_y=False,
            )

            # Forecast for points if available
            if "created_points" in forecast:
                created_points_ml = forecast["created_points"]["most_likely"]
                resolved_points_ml = forecast["resolved_points"]["most_likely"]

                fig.add_trace(
                    go.Scatter(
                        x=[next_week],
                        y=[created_points_ml],
                        name="Points Forecast (Created)",
                        mode="markers",
                        marker=dict(
                            size=10,
                            color="#ff8c00",
                            symbol="diamond-x",
                            line=dict(width=2, color="white"),
                        ),
                        hovertemplate="<b>%{x}</b><br>Forecast Points Created: %{y:.1f}<extra></extra>",
                        yaxis="y2",
                    ),
                    secondary_y=True,
                )

                fig.add_trace(
                    go.Scatter(
                        x=[next_week],
                        y=[resolved_points_ml],
                        name="Points Forecast (Resolved)",
                        mode="markers",
                        marker=dict(
                            size=10,
                            color="#20c997",
                            symbol="diamond-x",
                            line=dict(width=2, color="white"),
                        ),
                        hovertemplate="<b>%{x}</b><br>Forecast Points Resolved: %{y:.1f}<extra></extra>",
                        yaxis="y2",
                    ),
                    secondary_y=True,
                )

            # Add vertical line between historical and forecast
            # Position annotation away from toolbar to avoid overlap
            fig.add_vline(
                x=len(weeks) - 0.5,
                line_dash="dash",
                line_color="rgba(0, 0, 0, 0.3)",
            )

            # Add annotation separately for better positioning control
            fig.add_annotation(
                x=len(weeks) - 0.5,
                y=1.02,
                xref="x",
                yref="paper",
                text="Forecast",
                showarrow=False,
                font=dict(size=11, color="rgba(0, 0, 0, 0.6)"),
                xanchor="center",
                yanchor="bottom",
            )

    # Configure layout
    layout_config = get_mobile_chart_layout(viewport_size)

    # Remove xaxis/yaxis from layout_config to avoid conflicts
    layout_config_clean = {
        k: v for k, v in layout_config.items() if k not in ["xaxis", "yaxis", "yaxis2"]
    }

    # Set titles for both y-axes
    fig.update_yaxes(
        title_text="Bug Items Count",
        secondary_y=False,
        tickfont=dict(size=10 if viewport_size == "mobile" else 12),
    )
    fig.update_yaxes(
        title_text="Story Points",
        secondary_y=True,
        tickfont=dict(size=10 if viewport_size == "mobile" else 12),
    )

    fig.update_layout(
        title="Bug Investment: Items vs Story Points",
        xaxis=dict(
            title="Week",
            tickangle=-45 if viewport_size == "mobile" else 0,
            tickfont=dict(size=10 if viewport_size == "mobile" else 12),
        ),
        barmode="group",
        hovermode="x unified",
        **layout_config_clean,
    )

    # Add legend configuration - reduced bottom margin to minimize empty space
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h" if viewport_size == "mobile" else "v",
            yanchor="bottom",
            y=-0.25 if viewport_size == "mobile" else 1.0,  # Reduced from -0.4 to -0.25
            xanchor="left" if viewport_size == "mobile" else "left",
            x=0 if viewport_size == "mobile" else 1.02,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="rgba(0,0,0,0.1)",
            borderwidth=1,
        ),
    )

    return fig


def create_bug_forecast_chart(
    forecast: Dict[str, Any], viewport_size: str = "mobile"
) -> go.Figure:
    """
    Create bug resolution forecast chart with confidence intervals.

    Implements T098: Mobile-optimized forecast visualization showing
    optimistic/most_likely/pessimistic completion estimates.

    Args:
        forecast: Bug forecast dictionary from forecast_bug_resolution()
        viewport_size: "mobile", "tablet", or "desktop"

    Returns:
        Plotly figure with forecast timeline and confidence intervals
    """
    fig = go.Figure()

    # Check if forecast is valid
    if forecast.get("insufficient_data") or forecast.get("most_likely_weeks") is None:
        # Show empty state with message
        fig.add_annotation(
            text="Insufficient data to generate forecast<br>Need at least 4 weeks of history with bug resolutions",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14 if viewport_size == "mobile" else 16, color="#666"),
            align="center",
        )

        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=300 if viewport_size == "mobile" else 400,
            margin=dict(l=20, r=20, t=40, b=20),
        )
        return fig

    # Extract forecast data
    optimistic_weeks = forecast["optimistic_weeks"]
    most_likely_weeks = forecast["most_likely_weeks"]
    pessimistic_weeks = forecast["pessimistic_weeks"]

    optimistic_date = forecast.get("optimistic_date")
    most_likely_date = forecast.get("most_likely_date")
    pessimistic_date = forecast.get("pessimistic_date")

    # Create timeline data
    scenarios = ["Optimistic", "Most Likely", "Pessimistic"]
    weeks = [optimistic_weeks, most_likely_weeks, pessimistic_weeks]
    dates = [optimistic_date, most_likely_date, pessimistic_date]
    colors = ["#28a745", "#007bff", "#ffc107"]

    # Add bar chart for weeks
    fig.add_trace(
        go.Bar(
            x=scenarios,
            y=weeks,
            text=[f"{w} weeks" for w in weeks],
            textposition="outside",
            marker=dict(color=colors, opacity=0.8),
            hovertemplate="<b>%{x}</b><br>"
            + "Completion: %{customdata}<br>"
            + "Weeks: %{y}<br>"
            + "<extra></extra>",
            customdata=dates,
            name="Forecast",
        )
    )

    # Add confidence interval shading
    if pessimistic_weeks and optimistic_weeks:
        fig.add_shape(
            type="rect",
            x0=-0.5,
            x1=2.5,
            y0=optimistic_weeks,
            y1=pessimistic_weeks,
            fillcolor="rgba(0,123,255,0.1)",
            line=dict(width=0),
            layer="below",
        )

    # Configure layout
    height = 350 if viewport_size == "mobile" else 450
    font_size = 11 if viewport_size == "mobile" else 13

    fig.update_layout(
        title=dict(
            text=f"Bug Resolution Forecast<br><sub>Based on {forecast.get('open_bugs', 0)} open bugs</sub>",
            font=dict(size=14 if viewport_size == "mobile" else 18),
            x=0.5,
            xanchor="center",
        ),
        xaxis=dict(
            title="Scenario",
            titlefont=dict(size=font_size),
            tickfont=dict(size=font_size),
            showgrid=False,
        ),
        yaxis=dict(
            title="Weeks to Completion",
            titlefont=dict(size=font_size),
            tickfont=dict(size=font_size),
            gridcolor="rgba(0,0,0,0.1)",
            gridwidth=1,
            zeroline=True,
        ),
        height=height,
        margin=dict(
            l=50 if viewport_size == "mobile" else 70,
            r=20,
            t=80 if viewport_size == "mobile" else 100,
            b=50 if viewport_size == "mobile" else 70,
        ),
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x unified",
    )

    # Add annotation for insufficient data warning if < 4 weeks
    if forecast.get("insufficient_data"):
        fig.add_annotation(
            text="⚠️ Limited data - forecast may be less accurate",
            xref="paper",
            yref="paper",
            x=0.5,
            y=1.08 if viewport_size == "mobile" else 1.05,
            showarrow=False,
            font=dict(size=10 if viewport_size == "mobile" else 11, color="#ff6b6b"),
            align="center",
        )

    return fig
