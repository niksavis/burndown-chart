"""Bug analysis UI components.

Provides UI components for bug metrics display, charts, and analysis tab layout.
"""

from dash import html
import dash_bootstrap_components as dbc
from typing import Dict, List, Optional
from data.bug_insights import InsightSeverity
from ui.tooltip_utils import create_help_icon
from configuration.help_content import BUG_ANALYSIS_TOOLTIPS


def create_bug_metrics_cards(bug_metrics: Dict, forecast: Dict) -> html.Div:
    """Create compact bug metrics summary display with three cards in responsive layout.

    Args:
        bug_metrics: Bug metrics summary dictionary with:
            - total_bugs: Total bug count
            - open_bugs: Open bug count
            - closed_bugs: Closed bug count
            - resolution_rate: Resolution rate (0.0-1.0)
        forecast: Bug resolution forecast dictionary

    Returns:
        Div containing three metric cards (Resolution Rate, Open Bugs, Expected Resolution)
        arranged in one row on desktop (md+) and stacked on mobile
    """
    # Handle zero bugs case (T027)
    if not bug_metrics or bug_metrics.get("total_bugs", 0) == 0:
        return html.Div(
            [
                html.Div(
                    [
                        html.I(className="fas fa-info-circle me-2"),
                        html.Span("No bugs found in the current dataset."),
                    ],
                    className="alert alert-info mb-3",
                ),
            ]
        )

    # Extract metrics
    total_bugs = bug_metrics.get("total_bugs", 0)
    open_bugs = bug_metrics.get("open_bugs", 0)
    closed_bugs = bug_metrics.get("closed_bugs", 0)
    resolution_rate = bug_metrics.get("resolution_rate", 0.0)
    avg_resolution_days = bug_metrics.get("avg_resolution_time_days", 0)
    date_from = bug_metrics.get("date_from")
    date_to = bug_metrics.get("date_to")

    # Determine resolution rate color and status
    if resolution_rate >= 0.80:
        rate_color = "#28a745"  # Green
        rate_bg = "rgba(40, 167, 69, 0.1)"
        rate_border = "rgba(40, 167, 69, 0.2)"
        rate_status = "Excellent"
        rate_icon = "fa-check-circle"
    elif resolution_rate >= 0.70:
        rate_color = "#ffc107"  # Yellow
        rate_bg = "rgba(255, 193, 7, 0.1)"
        rate_border = "rgba(255, 193, 7, 0.2)"
        rate_status = "Good"
        rate_icon = "fa-exclamation-triangle"
    else:
        rate_color = "#dc3545"  # Red
        rate_bg = "rgba(220, 53, 69, 0.1)"
        rate_border = "rgba(220, 53, 69, 0.2)"
        rate_status = "Needs Attention"
        rate_icon = "fa-exclamation-circle"

    # Determine open bugs status
    if open_bugs == 0:
        open_color = "#28a745"
        open_bg = "rgba(40, 167, 69, 0.1)"
        open_border = "rgba(40, 167, 69, 0.2)"
        open_icon = "fa-check-circle"
    elif open_bugs <= 5:
        open_color = "#20c997"  # Teal
        open_bg = "rgba(32, 201, 151, 0.1)"
        open_border = "rgba(32, 201, 151, 0.2)"
        open_icon = "fa-bug"
    else:
        open_color = "#fd7e14"  # Orange
        open_bg = "rgba(253, 126, 20, 0.1)"
        open_border = "rgba(253, 126, 20, 0.2)"
        open_icon = "fa-folder-open"

    # Extract forecast data if available
    most_likely_weeks = forecast.get("most_likely_weeks", 0) if forecast else 0
    most_likely_date = forecast.get("most_likely_date", "") if forecast else ""
    avg_closure_rate = forecast.get("avg_closure_rate", 0.0) if forecast else 0.0
    insufficient_data = forecast.get("insufficient_data", True) if forecast else True
    weeks_analyzed = forecast.get("weeks_analyzed", 0) if forecast else 0

    # Format date for display
    from datetime import datetime

    def format_date(iso_date: str) -> str:
        if not iso_date:
            return "N/A"
        try:
            date_obj = datetime.fromisoformat(iso_date)
            return date_obj.strftime("%b %d, %Y")
        except (ValueError, AttributeError):
            return iso_date

    most_likely_date_formatted = format_date(most_likely_date)

    # Forecast colors based on weeks
    if not insufficient_data and open_bugs > 0:
        if most_likely_weeks <= 2:
            forecast_color = "#28a745"
            forecast_bg = "rgba(40, 167, 69, 0.1)"
            forecast_border = "rgba(40, 167, 69, 0.2)"
            forecast_icon = "fa-check-circle"
            forecast_status = "Soon"
        elif most_likely_weeks <= 4:
            forecast_color = "#20c997"
            forecast_bg = "rgba(32, 201, 151, 0.1)"
            forecast_border = "rgba(32, 201, 151, 0.2)"
            forecast_icon = "fa-calendar-check"
            forecast_status = "On Track"
        else:
            forecast_color = "#ffc107"
            forecast_bg = "rgba(255, 193, 7, 0.1)"
            forecast_border = "rgba(255, 193, 7, 0.2)"
            forecast_icon = "fa-calendar-alt"
            forecast_status = "Long Term"
    else:
        # Default colors for insufficient data or zero bugs
        forecast_color = "#6c757d"
        forecast_bg = "rgba(108, 117, 125, 0.1)"
        forecast_border = "rgba(108, 117, 125, 0.2)"
        forecast_icon = "fa-info-circle"
        forecast_status = "N/A"

    # Build the three-card responsive layout
    return html.Div(
        [
            dbc.Row(
                [
                    # Resolution Rate Card
                    dbc.Col(
                        [
                            html.Div(
                                className="compact-trend-indicator d-flex align-items-center p-2 rounded h-100",
                                style={
                                    "backgroundColor": rate_bg,
                                    "border": f"1px solid {rate_border}",
                                },
                                children=[
                                    html.Div(
                                        className="trend-icon me-2 d-flex align-items-center justify-content-center rounded-circle",
                                        style={
                                            "width": "32px",
                                            "height": "32px",
                                            "backgroundColor": "white",
                                            "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                                            "flexShrink": 0,
                                        },
                                        children=html.I(
                                            className=f"fas {rate_icon}",
                                            style={
                                                "color": rate_color,
                                                "fontSize": "0.9rem",
                                            },
                                        ),
                                    ),
                                    html.Div(
                                        style={"flexGrow": 1},
                                        children=[
                                            html.Div(
                                                className="d-flex justify-content-between align-items-baseline",
                                                children=[
                                                    html.Span(
                                                        [
                                                            "Resolution Rate",
                                                            create_help_icon(
                                                                "resolution-rate-help",
                                                                position="inline",
                                                            ),
                                                        ],
                                                        className="fw-medium",
                                                        style={"fontSize": "0.85rem"},
                                                    ),
                                                    html.Span(
                                                        f"{resolution_rate * 100:.1f}%",
                                                        style={
                                                            "color": rate_color,
                                                            "fontWeight": "600",
                                                            "fontSize": "0.9rem",
                                                        },
                                                    ),
                                                ],
                                            ),
                                            # Add tooltip for Resolution Rate
                                            dbc.Tooltip(
                                                BUG_ANALYSIS_TOOLTIPS["resolution_rate"],
                                                target="info-tooltip-resolution-rate-help",
                                                placement="top",
                                            ),
                                            html.Div(
                                                className="d-flex justify-content-between",
                                                style={
                                                    "fontSize": "0.75rem",
                                                    "color": "#6c757d",
                                                },
                                                children=[
                                                    html.Span(
                                                        f"{closed_bugs} closed / {total_bugs} total"
                                                    ),
                                                    html.Span(
                                                        rate_status,
                                                        style={"color": rate_color},
                                                    ),
                                                ],
                                            ),
                                            html.Div(
                                                style={
                                                    "fontSize": "0.7rem",
                                                    "color": "#6c757d",
                                                    "marginTop": "2px",
                                                    "fontStyle": "italic",
                                                },
                                                children=[
                                                    html.I(
                                                        className="fas fa-calendar-alt me-1",
                                                        style={"fontSize": "0.65rem"},
                                                    ),
                                                    html.Span(
                                                        f"{date_from.strftime('%b %d, %Y') if date_from else 'All time'} - {date_to.strftime('%b %d, %Y') if date_to else 'Now'}"
                                                    ),
                                                ]
                                                if date_from or date_to
                                                else [],
                                            ),
                                        ],
                                    ),
                                ],
                            )
                        ],
                        width=12,
                        md=4,
                        className="mb-2",
                    ),
                    # Open Bugs Card
                    dbc.Col(
                        [
                            html.Div(
                                className="compact-trend-indicator d-flex align-items-center p-2 rounded h-100",
                                style={
                                    "backgroundColor": open_bg,
                                    "border": f"1px solid {open_border}",
                                },
                                children=[
                                    html.Div(
                                        className="trend-icon me-2 d-flex align-items-center justify-content-center rounded-circle",
                                        style={
                                            "width": "32px",
                                            "height": "32px",
                                            "backgroundColor": "white",
                                            "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                                            "flexShrink": 0,
                                        },
                                        children=html.I(
                                            className=f"fas {open_icon}",
                                            style={
                                                "color": open_color,
                                                "fontSize": "0.9rem",
                                            },
                                        ),
                                    ),
                                    html.Div(
                                        style={"flexGrow": 1},
                                        children=[
                                            html.Div(
                                                className="d-flex justify-content-between align-items-baseline",
                                                children=[
                                                    html.Span(
                                                        [
                                                            "Open Bugs",
                                                            create_help_icon(
                                                                "open-bugs-help",
                                                                position="inline",
                                                            ),
                                                        ],
                                                        className="fw-medium",
                                                        style={"fontSize": "0.85rem"},
                                                    ),
                                                    html.Span(
                                                        f"{open_bugs}",
                                                        style={
                                                            "color": open_color,
                                                            "fontWeight": "600",
                                                            "fontSize": "0.9rem",
                                                        },
                                                    ),
                                                ],
                                            ),
                                            # Add tooltip for Open Bugs
                                            dbc.Tooltip(
                                                BUG_ANALYSIS_TOOLTIPS["open_bugs"],
                                                target="info-tooltip-open-bugs-help",
                                                placement="top",
                                            ),
                                            html.Div(
                                                style={
                                                    "fontSize": "0.75rem",
                                                    "color": "#6c757d",
                                                },
                                                children=[
                                                    html.Span(
                                                        f"Avg resolution: {avg_resolution_days:.1f} days"
                                                    )
                                                ],
                                            ),
                                            html.Div(
                                                style={
                                                    "fontSize": "0.7rem",
                                                    "color": "#6c757d",
                                                    "marginTop": "2px",
                                                    "fontStyle": "italic",
                                                },
                                                children=[
                                                    html.I(
                                                        className="fas fa-clock me-1",
                                                        style={"fontSize": "0.65rem"},
                                                    ),
                                                    html.Span(
                                                        "Current state (all time)"
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                ],
                            )
                        ],
                        width=12,
                        md=4,
                        className="mb-2",
                    ),
                    # Expected Resolution Card
                    dbc.Col(
                        [
                            html.Div(
                                className="compact-trend-indicator d-flex align-items-center p-2 rounded h-100",
                                style={
                                    "backgroundColor": forecast_bg,
                                    "border": f"1px solid {forecast_border}",
                                },
                                children=[
                                    html.Div(
                                        className="trend-icon me-2 d-flex align-items-center justify-content-center rounded-circle",
                                        style={
                                            "width": "32px",
                                            "height": "32px",
                                            "backgroundColor": "white",
                                            "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                                            "flexShrink": 0,
                                        },
                                        children=html.I(
                                            className=f"fas {forecast_icon}",
                                            style={
                                                "color": forecast_color,
                                                "fontSize": "0.9rem",
                                            },
                                        ),
                                    ),
                                    html.Div(
                                        style={"flexGrow": 1},
                                        children=[
                                            html.Div(
                                                className="d-flex justify-content-between align-items-baseline",
                                                children=[
                                                    html.Span(
                                                        [
                                                            "Expected Resolution",
                                                            create_help_icon(
                                                                "expected-resolution-help",
                                                                position="inline",
                                                            ),
                                                        ],
                                                        className="fw-medium",
                                                        style={"fontSize": "0.85rem"},
                                                    ),
                                                    html.Span(
                                                        f"~{most_likely_weeks} weeks"
                                                        if not insufficient_data
                                                        and open_bugs > 0
                                                        else "N/A",
                                                        style={
                                                            "color": forecast_color,
                                                            "fontWeight": "600",
                                                            "fontSize": "0.9rem",
                                                        },
                                                    ),
                                                ],
                                            ),
                                            # Add tooltip for Expected Resolution
                                            dbc.Tooltip(
                                                BUG_ANALYSIS_TOOLTIPS["expected_resolution"],
                                                target="info-tooltip-expected-resolution-help",
                                                placement="top",
                                            ),
                                            html.Div(
                                                className="d-flex justify-content-between",
                                                style={
                                                    "fontSize": "0.75rem",
                                                    "color": "#6c757d",
                                                },
                                                children=[
                                                    html.Span(
                                                        f"By {most_likely_date_formatted} • {avg_closure_rate:.1f} bugs/week"
                                                        if not insufficient_data
                                                        and open_bugs > 0
                                                        else (
                                                            "All bugs resolved!"
                                                            if open_bugs == 0
                                                            else "Insufficient data"
                                                        )
                                                    ),
                                                    html.Span(
                                                        forecast_status,
                                                        style={"color": forecast_color},
                                                    ),
                                                ],
                                            ),
                                            html.Div(
                                                style={
                                                    "fontSize": "0.7rem",
                                                    "color": "#6c757d",
                                                    "marginTop": "2px",
                                                    "fontStyle": "italic",
                                                },
                                                children=[
                                                    html.I(
                                                        className="fas fa-chart-line me-1",
                                                        style={"fontSize": "0.65rem"},
                                                    ),
                                                    html.Span(
                                                        f"Based on {weeks_analyzed} weeks of data"
                                                    ),
                                                ]
                                                if weeks_analyzed > 0
                                                else [],
                                            ),
                                        ],
                                    ),
                                ],
                            )
                        ],
                        width=12,
                        md=4,
                        className="mb-2",
                    ),
                ],
                className="g-2",
            ),
        ],
        className="mb-3",
    )


def create_quality_insights_panel(
    insights: List[Dict], weekly_stats: Optional[List[Dict]] = None
) -> dbc.Card:
    """Create quality insights panel with severity icons and expandable details.

    Args:
        insights: List of insight dictionaries with:
            - type: InsightType enum
            - severity: InsightSeverity enum
            - message: Short insight message
            - actionable_recommendation: Detailed recommendation
        weekly_stats: Optional list of weekly statistics for data sufficiency check

    Returns:
        Dash Bootstrap Components Card with quality insights
    """
    if not insights:
        # Check if we have weekly stats to provide better feedback
        weeks_available = len(weekly_stats) if weekly_stats else 0

        if weeks_available < 3:
            message = html.Div(
                [
                    html.I(className="fas fa-info-circle me-2"),
                    html.Div(
                        [
                            html.Strong("Insufficient data for insights"),
                            html.Br(),
                            html.Small(
                                f"Quality insights require at least 3 weeks of bug activity data. "
                                f"Currently: {weeks_available} week{'s' if weeks_available != 1 else ''} available. "
                                f"Increase the timeline filter or add more bug history.",
                                className="text-muted",
                            ),
                        ]
                    ),
                ],
                className="alert alert-info mb-0",
            )
        else:
            message = html.Div(
                [
                    html.I(className="fas fa-check-circle me-2 text-success"),
                    html.Span(
                        f"Quality is stable - no critical issues detected ({weeks_available} weeks analyzed)."
                    ),
                ],
                className="alert alert-success mb-0",
            )

        return dbc.Card(
            dbc.CardBody(
                [
                    html.H4("Quality Insights", className="card-title"),
                    message,
                ]
            ),
            className="mb-3",
        )

    def get_severity_config(severity: InsightSeverity) -> Dict:
        """Get icon and color configuration for severity level."""
        severity_configs = {
            InsightSeverity.CRITICAL: {
                "icon": "fa-exclamation-triangle",
                "color": "danger",
                "badge_text": "Critical",
            },
            InsightSeverity.HIGH: {
                "icon": "fa-exclamation-circle",
                "color": "warning",
                "badge_text": "High",
            },
            InsightSeverity.MEDIUM: {
                "icon": "fa-info-circle",
                "color": "info",
                "badge_text": "Medium",
            },
            InsightSeverity.LOW: {
                "icon": "fa-check-circle",
                "color": "success",
                "badge_text": "Low",
            },
        }
        return severity_configs.get(severity, severity_configs[InsightSeverity.LOW])

    # Create insight items with expandable details
    insight_items = []
    for idx, insight in enumerate(insights):
        severity_config = get_severity_config(insight["severity"])

        # Create collapse ID for this insight
        collapse_id = f"insight-collapse-{idx}"

        insight_item = dbc.Card(
            [
                dbc.CardHeader(
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.I(
                                        className=f"fas {severity_config['icon']} me-2"
                                    ),
                                    html.Span(insight["message"]),
                                ],
                                width=10,
                            ),
                            dbc.Col(
                                [
                                    dbc.Badge(
                                        severity_config["badge_text"],
                                        color=severity_config["color"],
                                        className="me-2",
                                    ),
                                    dbc.Button(
                                        html.I(className="fas fa-chevron-down"),
                                        id=f"insight-toggle-{idx}",
                                        color="link",
                                        size="sm",
                                        className="p-0",
                                    ),
                                ],
                                width=2,
                                className="text-end",
                            ),
                        ],
                        align="center",
                    ),
                    className=f"bg-{severity_config['color']} bg-opacity-10 border-{severity_config['color']}",
                    style={"cursor": "pointer"},
                    id=f"insight-header-{idx}",
                ),
                dbc.Collapse(
                    dbc.CardBody(
                        [
                            html.H6("Recommendation:", className="fw-bold mb-2"),
                            html.P(
                                insight["actionable_recommendation"],
                                className="mb-0",
                            ),
                        ]
                    ),
                    id=collapse_id,
                    is_open=False,
                ),
            ],
            className="mb-2",
        )
        insight_items.append(insight_item)

    return dbc.Card(
        dbc.CardBody(
            [
                html.H4(
                    [
                        html.I(className="fas fa-lightbulb me-2"),
                        "Quality Insights",
                    ],
                    className="card-title mb-3",
                ),
                html.Div(insight_items),
            ]
        ),
        className="mb-3",
    )


def create_bug_forecast_card(forecast: Dict, open_bugs: int) -> html.Div:
    """Create compact bug resolution forecast display (indicator-style).

    Args:
        forecast: Forecast dictionary with:
            - most_likely_weeks: Expected weeks to resolution
            - most_likely_date: Expected completion date (ISO format)
            - avg_closure_rate: Average bugs resolved per week
            - insufficient_data: True if forecast cannot be calculated
        open_bugs: Number of currently open bugs

    Returns:
        Div with compact forecast indicator
    """
    # Handle insufficient data case
    if forecast.get("insufficient_data", False):
        return html.Div(
            [
                html.Div(
                    [
                        html.I(className="fas fa-info-circle me-2"),
                        html.Span(
                            "Insufficient data for forecasting. Need at least 4 weeks of bug resolution history."
                        ),
                    ],
                    className="alert alert-warning mb-3",
                    style={"fontSize": "0.85rem", "padding": "0.5rem 1rem"},
                ),
            ]
        )

    # Handle zero open bugs
    if open_bugs == 0:
        return html.Div(
            [
                html.Div(
                    [
                        html.I(className="fas fa-check-circle me-2 text-success"),
                        html.Span("All bugs resolved! No open bugs remaining."),
                    ],
                    className="alert alert-success mb-3",
                    style={"fontSize": "0.85rem", "padding": "0.5rem 1rem"},
                ),
            ]
        )

    # Extract forecast data
    most_likely_weeks = forecast.get("most_likely_weeks", 0)
    most_likely_date = forecast.get("most_likely_date", "")
    avg_closure_rate = forecast.get("avg_closure_rate", 0.0)

    # Format date for display (YYYY-MM-DD -> Mon DD, YYYY)
    from datetime import datetime

    def format_date(iso_date: str) -> str:
        """Format ISO date for display."""
        if not iso_date:
            return "N/A"
        try:
            date_obj = datetime.fromisoformat(iso_date)
            return date_obj.strftime("%b %d, %Y")
        except (ValueError, AttributeError):
            return iso_date

    most_likely_date_formatted = format_date(most_likely_date)

    # Determine color based on weeks
    if most_likely_weeks <= 2:
        forecast_color = "#28a745"  # Green
        forecast_bg = "rgba(40, 167, 69, 0.1)"
        forecast_border = "rgba(40, 167, 69, 0.2)"
        forecast_icon = "fa-check-circle"
        forecast_status = "Soon"
    elif most_likely_weeks <= 4:
        forecast_color = "#20c997"  # Teal
        forecast_bg = "rgba(32, 201, 151, 0.1)"
        forecast_border = "rgba(32, 201, 151, 0.2)"
        forecast_icon = "fa-calendar-check"
        forecast_status = "On Track"
    else:
        forecast_color = "#ffc107"  # Yellow
        forecast_bg = "rgba(255, 193, 7, 0.1)"
        forecast_border = "rgba(255, 193, 7, 0.2)"
        forecast_icon = "fa-calendar-alt"
        forecast_status = "Long Term"

    return html.Div(
        [
            # Compact forecast indicator
            html.Div(
                className="compact-trend-indicator d-flex align-items-center p-2 rounded mb-3",
                style={
                    "backgroundColor": forecast_bg,
                    "border": f"1px solid {forecast_border}",
                },
                children=[
                    html.Div(
                        className="trend-icon me-2 d-flex align-items-center justify-content-center rounded-circle",
                        style={
                            "width": "32px",
                            "height": "32px",
                            "backgroundColor": "white",
                            "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                            "flexShrink": 0,
                        },
                        children=html.I(
                            className=f"fas {forecast_icon}",
                            style={"color": forecast_color, "fontSize": "0.9rem"},
                        ),
                    ),
                    html.Div(
                        style={"flexGrow": 1},
                        children=[
                            html.Div(
                                className="d-flex justify-content-between align-items-baseline",
                                children=[
                                    html.Span(
                                        "Expected Resolution",
                                        className="fw-medium",
                                        style={"fontSize": "0.85rem"},
                                    ),
                                    html.Span(
                                        f"~{most_likely_weeks} weeks",
                                        style={
                                            "color": forecast_color,
                                            "fontWeight": "600",
                                            "fontSize": "0.9rem",
                                        },
                                    ),
                                ],
                            ),
                            html.Div(
                                className="d-flex justify-content-between",
                                style={"fontSize": "0.75rem", "color": "#6c757d"},
                                children=[
                                    html.Span(
                                        f"{most_likely_date_formatted} • {avg_closure_rate:.1f} bugs/week"
                                    ),
                                    html.Span(
                                        forecast_status, style={"color": forecast_color}
                                    ),
                                ],
                            ),
                            # Analysis period information
                            html.Div(
                                style={
                                    "fontSize": "0.7rem",
                                    "color": "#6c757d",
                                    "marginTop": "2px",
                                    "fontStyle": "italic",
                                },
                                children=[
                                    html.I(
                                        className="fas fa-chart-line me-1",
                                        style={"fontSize": "0.65rem"},
                                    ),
                                    html.Span(
                                        f"Based on {forecast.get('weeks_analyzed', 0)} weeks of resolution data"
                                    ),
                                ]
                                if forecast.get("weeks_analyzed")
                                else [],
                            ),
                        ],
                    ),
                ],
            ),
        ]
    )


def create_bug_analysis_tab() -> html.Div:
    """Create bug analysis tab layout placeholder.

    Returns a simple placeholder div that will be populated by the callback.
    This matches the pattern used by other tabs (Items per Week, etc.) where
    the entire tab content is returned by a callback instead of using nested
    placeholder divs.

    Returns:
        Dash HTML Div placeholder for bug analysis tab content
    """
    return html.Div(
        id="bug-analysis-tab-content",
        children=html.Div("Loading bug analysis...", className="text-center p-5"),
    )
