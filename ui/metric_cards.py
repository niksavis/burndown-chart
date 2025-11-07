"""Reusable metric card components for DORA and Flow metrics.

This module provides functions to create metric display cards with support for:
- Success state with performance tier indicators
- Error states with actionable guidance
- Loading states
- Responsive design (mobile-first)
"""

from typing import Any, Dict, List, Optional

import dash_bootstrap_components as dbc
from dash import html

from ui.tooltip_utils import create_info_tooltip


def _create_mini_bar_sparkline(
    data: List[float], color: str, height: int = 40
) -> html.Div:
    """Create a mini CSS-based bar sparkline for inline trend display.

    Args:
        data: List of numeric values to display
        color: CSS color for bars
        height: Maximum height of bars in pixels

    Returns:
        Div containing mini bar chart
    """
    if not data or len(data) < 2:
        return html.Div()

    max_val = max(data) if max(data) > 0 else 1
    normalized = [v / max_val for v in data]

    bars = []
    for i, val in enumerate(normalized):
        bar_height = max(val * height, 2)
        opacity = 0.5 + (i / len(normalized)) * 0.5  # Fade from 0.5 to 1.0

        bars.append(
            html.Div(
                style={
                    "width": "4px",
                    "height": f"{bar_height}px",
                    "backgroundColor": color,
                    "opacity": opacity,
                    "borderRadius": "2px",
                    "margin": "0 1px",
                }
            )
        )

    return html.Div(
        bars,
        className="d-flex align-items-end justify-content-center",
        style={"height": f"{height}px", "gap": "1px"},
    )


def _create_detailed_chart(
    metric_name: str,
    display_name: str,
    weekly_labels: List[str],
    weekly_values: List[float],
    metric_data: Dict[str, Any],
    sparkline_color: str,
) -> Any:
    """Create detailed chart for metric card collapse section.

    Special handling for:
    - deployment_frequency: Shows dual lines (deployments vs releases) and details table
    - change_failure_rate: Shows dual lines (deployment CFR vs release CFR)
    For other metrics, shows standard single-line chart.

    Args:
        metric_name: Internal metric name (e.g., "deployment_frequency", "change_failure_rate")
        display_name: Display name for chart title
        weekly_labels: Week labels
        weekly_values: Primary metric values
        metric_data: Full metric data dict with potential weekly_release_values
        sparkline_color: Color for the chart

    Returns:
        Div containing chart and optional details table
    """
    from visualization.metric_trends import (
        create_metric_trend_sparkline,
        create_dual_line_trend,
    )

    # Special case 1: deployment_frequency with release tracking
    if metric_name == "deployment_frequency" and "weekly_release_values" in metric_data:
        weekly_release_values = metric_data.get("weekly_release_values", [])
        chart = create_dual_line_trend(
            week_labels=weekly_labels,
            deployment_values=weekly_values,
            release_values=weekly_release_values,
            height=250,
            show_axes=True,
        )

        # Add deployment details table
        details_table = _create_deployment_details_table(
            metric_data=metric_data,
            weekly_labels=weekly_labels,
            weekly_deployments=weekly_values,
            weekly_releases=weekly_release_values,
        )

        return html.Div([chart, details_table])

    # Special case 2: change_failure_rate with release tracking
    if metric_name == "change_failure_rate" and "weekly_release_values" in metric_data:
        weekly_release_values = metric_data.get("weekly_release_values", [])
        # Reuse dual line chart but with different labels
        chart = create_dual_line_trend(
            week_labels=weekly_labels,
            deployment_values=weekly_values,
            release_values=weekly_release_values,
            height=250,
            show_axes=True,
        )

        # Customize the chart for CFR context with a note
        cfr_note = html.Div(
            [
                html.Hr(className="my-2"),
                html.Small(
                    [
                        html.I(className="fas fa-info-circle me-1 text-info"),
                        "Blue line shows deployment-based CFR (operational tasks), ",
                        "Green line shows release-based CFR (unique fixVersions). ",
                        "Release-based CFR avoids double-counting failures for the same release.",
                    ],
                    className="text-muted",
                ),
            ],
            className="text-center",
        )

        return html.Div([chart, cfr_note])

    # Standard single-line chart for other metrics
    # Use full trend chart with performance zones for DORA metrics
    from visualization.metric_trends import create_metric_trend_full

    is_dora_metric = metric_name in [
        "deployment_frequency",
        "lead_time_for_changes",
        "change_failure_rate",
        "mean_time_to_recovery",
    ]

    if is_dora_metric:
        # Use full chart with performance tier zones
        return create_metric_trend_full(
            week_labels=weekly_labels,
            values=weekly_values,
            metric_name=metric_name,  # Use internal name for zone matching
            unit=metric_data.get("unit", ""),
            height=250,
            show_performance_zones=True,
        )
    else:
        # Use sparkline for Flow metrics
        return create_metric_trend_sparkline(
            week_labels=weekly_labels,
            values=weekly_values,
            metric_name=display_name,
            unit=metric_data.get("unit", ""),
            height=200,
            show_axes=True,
            color=sparkline_color,
        )


def _create_deployment_details_table(
    metric_data: Dict[str, Any],
    weekly_labels: List[str],
    weekly_deployments: List[float],
    weekly_releases: List[float],
) -> html.Div:
    """Create details table showing release names per week.

    Args:
        metric_data: Full metric data with weekly_release_names
        weekly_labels: Week labels
        weekly_deployments: Deployment counts per week
        weekly_releases: Release counts per week

    Returns:
        Div containing summary and table
    """
    # Calculate ratio stats
    total_deployments = sum(weekly_deployments)
    total_releases = sum(weekly_releases)
    ratio = total_deployments / total_releases if total_releases > 0 else 0

    # Create summary
    summary = html.Div(
        [
            html.Hr(className="my-3"),
            html.H6("Deployment Details", className="text-center mb-2"),
            html.Div(
                [
                    html.Small(
                        [
                            f"Total: {int(total_deployments)} deployments • ",
                            f"{int(total_releases)} releases • ",
                            f"Ratio: {ratio:.1f}:1",
                        ],
                        className="text-muted",
                    ),
                ],
                className="text-center mb-3",
            ),
        ]
    )

    # Get release names from snapshots (need to load from cache)
    # For now, show a simple week-by-week breakdown
    table_rows = []

    for i, week in enumerate(weekly_labels):
        if i < len(weekly_deployments) and i < len(weekly_releases):
            deployments = int(weekly_deployments[i])
            releases = int(weekly_releases[i])

            if deployments > 0 or releases > 0:
                week_ratio = deployments / releases if releases > 0 else deployments

                table_rows.append(
                    html.Tr(
                        [
                            html.Td(week, style={"fontSize": "0.85rem"}),
                            html.Td(
                                str(deployments),
                                className="text-center",
                                style={"fontSize": "0.85rem"},
                            ),
                            html.Td(
                                str(releases),
                                className="text-center",
                                style={"fontSize": "0.85rem"},
                            ),
                            html.Td(
                                f"{week_ratio:.1f}:1",
                                className="text-center",
                                style={"fontSize": "0.85rem"},
                            ),
                        ]
                    )
                )

    if not table_rows:
        table_content = html.Div(
            html.Small(
                "No deployment activity in selected period", className="text-muted"
            ),
            className="text-center my-2",
        )
    else:
        table_content = html.Table(
            [
                html.Thead(
                    html.Tr(
                        [
                            html.Th("Week", style={"fontSize": "0.85rem"}),
                            html.Th(
                                "Deployments",
                                className="text-center",
                                style={"fontSize": "0.85rem"},
                            ),
                            html.Th(
                                "Releases",
                                className="text-center",
                                style={"fontSize": "0.85rem"},
                            ),
                            html.Th(
                                "Ratio",
                                className="text-center",
                                style={"fontSize": "0.85rem"},
                            ),
                        ]
                    )
                ),
                html.Tbody(table_rows),
            ],
            className="table table-sm table-hover",
            style={"fontSize": "0.85rem"},
        )

    return html.Div([summary, table_content])


def create_metric_card(metric_data: dict, card_id: Optional[str] = None) -> dbc.Card:
    """Create a metric display card.

    Args:
        metric_data: Dictionary with metric information:
            {
                "metric_name": str,
                "value": float | None,
                "unit": str,
                "performance_tier": str | None,  # Elite/High/Medium/Low
                "performance_tier_color": str,   # green/yellow/orange/red
                "error_state": str,              # success/missing_mapping/no_data/calculation_error
                "error_message": str | None,
                "excluded_issue_count": int,
                "total_issue_count": int,
                "details": dict
            }
        card_id: Optional HTML ID for the card

    Returns:
        Dash Bootstrap Card component

    Example:
        >>> metric_data = {
        ...     "metric_name": "deployment_frequency",
        ...     "value": 45.2,
        ...     "unit": "deployments/month",
        ...     "performance_tier": "High",
        ...     "performance_tier_color": "yellow",
        ...     "error_state": "success",
        ...     "total_issue_count": 50
        ... }
        >>> card = create_metric_card(metric_data)
    """
    # Determine if error state
    error_state = metric_data.get("error_state", "success")

    if error_state != "success":
        return _create_error_card(metric_data, card_id)

    return _create_success_card(metric_data, card_id)


def _create_success_card(metric_data: dict, card_id: Optional[str]) -> dbc.Card:
    """Create card for successful metric calculation.

    Now includes inline trend sparkline (always visible) below the metric value.
    Trend data should be provided in metric_data as:
    - weekly_labels: List of week labels (e.g., ["2025-W40", "2025-W41", ...])
    - weekly_values: List of metric values for each week
    """
    from visualization.metric_trends import (
        create_metric_trend_sparkline,
        create_dual_line_trend,
        create_metric_trend_full,
    )

    # Map performance tier colors to Bootstrap colors
    tier_color_map = {
        "green": "success",
        "yellow": "warning",
        "orange": "warning",
        "red": "danger",
    }

    tier_color = metric_data.get("performance_tier_color", "secondary")

    # Special handling for Flow Load (WIP) - apply health-based color coding
    metric_name = metric_data.get("metric_name", "Unknown Metric")
    value = metric_data.get("value")

    if metric_name == "flow_load" and value is not None:
        # Override tier_color with WIP health thresholds
        # These thresholds can be made configurable later
        if value < 10:
            tier_color = "green"  # Healthy
        elif value < 20:
            tier_color = "yellow"  # Warning
        elif value < 30:
            tier_color = "orange"  # High
        else:
            tier_color = "red"  # Critical

    bootstrap_color = tier_color_map.get(tier_color, "secondary")
    alternative_name = metric_data.get("alternative_name")
    metric_tooltip = metric_data.get("tooltip")  # Optional tooltip text

    if alternative_name:
        display_name = alternative_name
        tooltip_text = f"Interpreted as: {alternative_name} (Standard field: {metric_name.replace('_', ' ').title()})"
    else:
        display_name = metric_name.replace("_", " ").title()
        tooltip_text = None

    # Format value - special handling for deployment_frequency with release count
    value = metric_data.get("value")
    release_value = metric_data.get("release_value")  # NEW: for deployment_frequency
    p95_value = metric_data.get("p95_value")  # NEW: for lead_time and mttr
    mean_value = metric_data.get("mean_value")  # NEW: for lead_time and mttr

    if value is not None:
        formatted_value = f"{value:.1f}" if value >= 10 else f"{value:.2f}"
    else:
        formatted_value = "N/A"

    # Format release value if present (deployment_frequency metric)
    if release_value is not None:
        formatted_release_value = (
            f"{release_value:.1f}" if release_value >= 10 else f"{release_value:.2f}"
        )
    else:
        formatted_release_value = None

    # Format P95 value if present (lead_time and mttr metrics)
    if p95_value is not None:
        formatted_p95_value = (
            f"{p95_value:.1f}" if p95_value >= 10 else f"{p95_value:.2f}"
        )
    else:
        formatted_p95_value = None

    # Build card with h-100 for consistent heights with error cards
    card_props = {"className": "metric-card mb-3 h-100"}
    if card_id:
        card_props["id"] = card_id

    # Build card header with flex layout for title on left, badge on right
    if alternative_name:
        title_element = html.Span(
            [
                html.I(
                    className="fas fa-info-circle me-2 text-info",
                    title=tooltip_text,
                ),
                display_name,
            ],
            className="metric-card-title",
        )
    else:
        # Start with just the display name
        title_content = [display_name]

        # Add info tooltip if provided
        if metric_tooltip:
            title_content.extend(
                [
                    " ",
                    create_info_tooltip(
                        help_text=metric_tooltip,
                        id_suffix=f"metric-{metric_name}",
                        placement="top",
                        variant="dark",
                    ),
                ]
            )

        title_element = html.Span(title_content, className="metric-card-title")

    # Build header with flex layout
    # Special badge for Flow Load (WIP) showing health status
    if metric_name == "flow_load" and value is not None:
        if value < 10:
            badge_text = "Healthy"
        elif value < 20:
            badge_text = "Warning"
        elif value < 30:
            badge_text = "High"
        else:
            badge_text = "Critical"

        badge_element = dbc.Badge(
            badge_text,
            color=bootstrap_color,
            className="ms-auto",
            style={"fontSize": "0.75rem", "fontWeight": "600"},
        )
    else:
        # Regular badge for other metrics
        badge_element = (
            dbc.Badge(
                metric_data.get("performance_tier", "Unknown"),
                color=bootstrap_color,
                className="ms-auto",
                style={"fontSize": "0.75rem", "fontWeight": "600"},
            )
            if metric_data.get("performance_tier")
            else None
        )

    header_children: List[Any] = [
        html.Div(
            [
                title_element,
                badge_element,
            ],
            className="d-flex align-items-center justify-content-between w-100",
        )
    ]

    card_header = dbc.CardHeader(header_children)

    # Build card body with inline trend sparkline
    card_body_children = [
        # Metric value (large, centered)
        html.H2(formatted_value, className="text-center metric-value mb-2"),
        # Unit (smaller, centered)
        html.P(
            metric_data.get("unit", ""),
            className="text-muted text-center metric-unit mb-1",
        ),
    ]

    # Add trend indicator with percentage change
    weekly_labels = metric_data.get("weekly_labels", [])
    weekly_values = metric_data.get("weekly_values", [])

    trend_added = False  # Track if we added a trend indicator

    if weekly_values and len(weekly_values) >= 2:
        # Calculate trend: compare most recent value to median of previous values
        current_value = weekly_values[-1]
        previous_values = weekly_values[:-1]
        if previous_values:
            previous_avg = sum(previous_values) / len(previous_values)
            # Handle case where average is 0 (but we still want to show trend)
            if previous_avg > 0:
                percent_change = ((current_value - previous_avg) / previous_avg) * 100
            elif current_value > 0:
                # If previous was 0 but current is non-zero, show large increase
                percent_change = 100.0
            elif current_value == 0 and previous_avg == 0:
                # Both zero - show neutral/no change
                percent_change = 0.0
            else:
                # Current is 0 but previous was non-zero (shouldn't happen if previous_avg > 0 check failed)
                percent_change = -100.0

            # Determine if trend is good based on metric type
            # For deployment_frequency: higher is better (green up, red down)
            # For lead_time, mttr, cfr: lower is better (green down, red up)
            is_higher_better = metric_name in ["deployment_frequency"]

            # Show neutral/stable indicator for no change (exactly 0.0%)
            if percent_change == 0.0:
                trend_color = "secondary"
                trend_icon = "fas fa-arrow-right"
                trend_text = "0.0% vs prev avg"
            elif is_higher_better:
                # Higher is better metrics
                if percent_change > 0:
                    trend_color = "success"
                    trend_icon = "fas fa-arrow-up"
                else:
                    trend_color = "danger"
                    trend_icon = "fas fa-arrow-down"
                trend_text = f"{abs(percent_change):.1f}% vs prev avg"
            else:
                # Lower is better metrics
                if percent_change < 0:
                    trend_color = "success"
                    trend_icon = "fas fa-arrow-down"
                else:
                    trend_color = "danger"
                    trend_icon = "fas fa-arrow-up"
                trend_text = f"{abs(percent_change):.1f}% vs prev avg"

            # Show neutral color for very small changes (< 5% but not exactly 0)
            if abs(percent_change) < 5 and percent_change != 0.0:
                trend_color = "secondary"
                trend_icon = "fas fa-minus"

            card_body_children.append(
                html.Div(
                    [
                        html.I(className=f"{trend_icon} me-1"),
                        html.Span(trend_text),
                    ],
                    className=f"text-center text-{trend_color} small mb-2",
                    style={"fontWeight": "500"},
                )
            )
            trend_added = True

    # Add placeholder if no trend was added (maintains consistent card height)
    if not trend_added:
        card_body_children.append(
            html.Div(
                [
                    html.I(className="fas fa-minus me-1"),
                    html.Span("No trend data yet"),
                ],
                className="text-center text-muted small mb-2",
                style={"fontWeight": "500"},
            )
        )

    # Add release count for deployment_frequency and change_failure_rate metrics
    # Add P95 for lead_time_for_changes and mean_time_to_recovery metrics
    if formatted_release_value is not None and metric_name in [
        "deployment_frequency",
        "change_failure_rate",
    ]:
        # Determine text and icon based on metric type
        release_config = {
            "deployment_frequency": {
                "text": f"{formatted_release_value} releases/week",
                "icon": "fas fa-code-branch me-1",
            },
            "change_failure_rate": {
                "text": f"{formatted_release_value}% release CFR",
                "icon": "fas fa-code-branch me-1",
            },
        }

        config = release_config.get(metric_name, {})
        if config:
            card_body_children.append(
                html.Div(
                    [
                        html.I(className=config["icon"]),
                        html.Span(config["text"]),
                    ],
                    className="text-center text-muted small mb-2",
                )
            )

    # Add P95 information for lead_time_for_changes and mean_time_to_recovery
    elif formatted_p95_value is not None and metric_name in [
        "lead_time_for_changes",
        "mean_time_to_recovery",
    ]:
        # Determine text and icon based on metric type
        p95_config = {
            "lead_time_for_changes": {
                "text": f"{formatted_p95_value}d P95 (95% faster)",
                "icon": "fas fa-chart-line me-1",
            },
            "mean_time_to_recovery": {
                "text": f"{formatted_p95_value}h P95 (95% faster)",
                "icon": "fas fa-chart-line me-1",
            },
        }

        config = p95_config.get(metric_name, {})
        if config:
            card_body_children.append(
                html.Div(
                    [
                        html.I(className=config["icon"]),
                        html.Span(config["text"]),
                    ],
                    className="text-center text-muted small mb-2",
                )
            )

    # Add inline trend sparkline if weekly data is provided
    # Note: weekly_labels and weekly_values already fetched above for trend indicator
    if weekly_labels and weekly_values and len(weekly_labels) > 1:
        # Determine color based on performance tier
        sparkline_color = {
            "green": "#28a745",
            "yellow": "#ffc107",
            "orange": "#fd7e14",
            "red": "#dc3545",
        }.get(tier_color, "#1f77b4")

        # Create inline mini sparkline (CSS-based, compact)
        mini_sparkline = _create_mini_bar_sparkline(
            weekly_values, sparkline_color, height=40
        )

        # Generate unique collapse ID for this card
        collapse_id = f"{metric_name}-details-collapse"

        card_body_children.append(
            html.Div(
                [
                    html.Hr(className="my-2"),
                    html.Div(
                        [
                            html.Small(
                                f"Trend (last {len(weekly_values)} weeks):",
                                className="text-muted d-block mb-1",
                            ),
                            mini_sparkline,
                            dbc.Button(
                                [
                                    html.I(className="fas fa-chart-line me-2"),
                                    "Show Details",
                                ],
                                id=f"{metric_name}-details-btn",
                                color="link",
                                size="sm",
                                className="mt-2 p-0",
                                style={"fontSize": "0.85rem"},
                            ),
                        ],
                        className="text-center",
                    ),
                    # Expandable detailed chart section
                    dbc.Collapse(
                        dbc.CardBody(
                            [
                                html.H6(
                                    f"Weekly {display_name} Trend",
                                    className="mb-3 text-center",
                                ),
                                # Special handling for deployment_frequency to show dual lines
                                _create_detailed_chart(
                                    metric_name=metric_name,
                                    display_name=display_name,
                                    weekly_labels=weekly_labels,
                                    weekly_values=weekly_values,
                                    metric_data=metric_data,
                                    sparkline_color=sparkline_color,
                                ),
                                html.Div(
                                    [
                                        html.Small(
                                            "Click chart to interact • Hover for values • Double-click to reset zoom",
                                            className="text-muted",
                                        )
                                    ],
                                    className="text-center mt-2",
                                ),
                            ],
                            className="bg-light",
                        ),
                        id=collapse_id,
                        is_open=False,
                    ),
                ],
                className="metric-trend-section",
            )
        )

    # Additional info at bottom
    card_body_children.extend(
        [
            html.Hr(className="my-2"),
            html.Small(
                _format_additional_info(metric_data),
                className="text-muted d-block text-center",
            ),
        ]
    )

    card_body = dbc.CardBody(card_body_children)

    return dbc.Card([card_header, card_body], **card_props)  # type: ignore[call-arg]


def _create_error_card(metric_data: dict, card_id: Optional[str]) -> dbc.Card:
    """Create card for error state with actionable guidance.

    Updated to match h-100 layout of success cards for consistent card heights.
    """
    error_state = metric_data.get("error_state", "unknown_error")
    error_message = metric_data.get("error_message", "An error occurred")

    # Format metric name for display
    metric_name = metric_data.get("metric_name", "Unknown Metric")
    display_name = metric_name.replace("_", " ").title()

    # Map error states to icons and titles
    error_config = {
        "missing_mapping": {
            "icon": "fas fa-cog",
            "title": "Field Mapping Required",
            "color": "warning",
            "action_text": "Configure Mappings",
            "action_id": {
                "type": "open-field-mapping",
                "index": metric_name,
            },  # Pattern-matching ID
            "message_override": "Configure JIRA field mappings in Settings to enable this metric.",
        },
        "no_data": {
            "icon": "fas fa-inbox",
            "title": "No Data Available",
            "color": "secondary",
            "action_text": "Recalculate Metrics",
            "action_id": "open-time-period-selector",
            "message_override": "No data found for the selected time period. Try recalculating metrics or adjusting the time range.",
        },
        "calculation_error": {
            "icon": "fas fa-exclamation-triangle",
            "title": "Calculation Error",
            "color": "danger",
            "action_text": "Retry Calculation",
            "action_id": "retry-metric-calculation",
        },
    }

    config = error_config.get(
        error_state,
        {
            "icon": "fas fa-exclamation-circle",
            "title": "Error",
            "color": "warning",
            "action_text": "View Details",
            "action_id": "view-error-details",
        },
    )

    # Build card with consistent h-100 class for equal heights
    card_props = {"className": "metric-card metric-card-error mb-3 h-100"}
    if card_id:
        card_props["id"] = card_id

    # Determine badge text based on error state
    badge_text_map = {
        "no_data": "No Data",
        "missing_mapping": "Setup Required",
        "calculation_error": "Error",
    }
    badge_text = badge_text_map.get(error_state, "Error")

    card_header = dbc.CardHeader(
        [
            html.Span(display_name, className="metric-card-title"),
            dbc.Badge(badge_text, color=config["color"], className="float-end"),
        ]
    )

    card_body = dbc.CardBody(
        [
            # Icon and title (compact layout)
            html.Div(
                [
                    html.I(
                        className=f"{config['icon']} fa-2x text-{config['color']} mb-2"
                    ),
                    html.H2("—", className="text-center metric-value mb-1 text-muted"),
                    html.P(
                        config["title"],
                        className="text-muted text-center metric-unit mb-2",
                    ),
                ],
                className="text-center",
            ),
            # Divider matching success cards
            html.Hr(className="my-2"),
            # Error message (compact)
            html.Small(
                config.get("message_override", error_message),
                className="text-muted d-block text-center",
            ),
        ],
        className="d-flex flex-column",
    )

    return dbc.Card([card_header, card_body], **card_props)  # type: ignore[call-arg]


def _format_additional_info(metric_data: dict) -> str:
    """Format additional information text for metric card."""
    total_issues = metric_data.get("total_issue_count", 0)
    excluded_issues = metric_data.get("excluded_issue_count", 0)

    if excluded_issues > 0:
        return (
            f"Based on {total_issues - excluded_issues} of {total_issues} issues. "
            f"{excluded_issues} excluded due to missing data."
        )
    else:
        return f"Based on {total_issues} issues"


def create_loading_card(metric_name: str) -> dbc.Card:
    """Create a loading placeholder card.

    Args:
        metric_name: Name of the metric being calculated

    Returns:
        Card with loading spinner
    """
    display_name = metric_name.replace("_", " ").title()

    return dbc.Card(
        [
            dbc.CardHeader(display_name),
            dbc.CardBody(
                [
                    dbc.Spinner(size="lg", color="primary"),
                    html.P("Calculating...", className="text-muted text-center mt-3"),
                ],
                className="text-center",
            ),
        ],
        className="metric-card metric-card-loading mb-3",
    )


def create_metric_cards_grid(
    metrics_data: Dict[str, dict], tooltips: Optional[Dict[str, str]] = None
) -> dbc.Row:
    """Create a responsive grid of metric cards.

    Args:
        metrics_data: Dictionary mapping metric names to metric data
            Example:
            {
                "deployment_frequency": {...},
                "lead_time_for_changes": {...}
            }
        tooltips: Optional dictionary mapping metric names to tooltip text
            Example:
            {
                "flow_velocity": "Number of work items completed per week...",
                "flow_time": "Median time from work start to completion..."
            }

    Returns:
        Dash Bootstrap Row with responsive columns
    """
    cards = []
    for metric_name, metric_info in metrics_data.items():
        # Add tooltip to metric_info if provided
        if tooltips and metric_name in tooltips:
            metric_info = {**metric_info, "tooltip": tooltips[metric_name]}

        card = create_metric_card(metric_info, card_id=f"{metric_name}-card")
        # Responsive column: full width on mobile, half on tablet, quarter on desktop
        col = dbc.Col(card, width=12, md=6, lg=3)
        cards.append(col)

    return dbc.Row(cards, className="metric-cards-grid mb-4")
