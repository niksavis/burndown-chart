"""Sub-component builders extracted from the success card assembly.

These functions encapsulate discrete visual sections of the metric card,
keeping _create_success_card focused on orchestration rather than detail.
"""

from typing import Any

import dash_bootstrap_components as dbc
from dash import html

from ui.metric_cards._helpers import _create_mini_bar_sparkline, _get_metric_explanation
from ui.tooltip_utils import create_info_tooltip


def _build_title_element(
    metric_name: str,
    display_name: str,
    alternative_name: str | None,
    metric_tooltip: str | None,
) -> html.Span:
    """Build the card title span with inline tooltip."""
    if metric_tooltip:
        help_text = metric_tooltip
    else:
        help_text = _get_metric_explanation(metric_name)

    if alternative_name:
        return html.Span(
            [
                display_name,
                " ",
                create_info_tooltip(
                    help_text=help_text,
                    id_suffix=f"metric-{metric_name}",
                    placement="top",
                    variant="dark",
                ),
            ],
            className="metric-card-title",
        )

    title_content: list[Any] = [display_name]
    title_content.extend(
        [
            " ",
            create_info_tooltip(
                help_text=help_text,
                id_suffix=f"metric-{metric_name}",
                placement="top",
                variant="dark",
            ),
        ]
    )
    return html.Span(title_content, className="metric-card-title")


def _build_card_badge(
    metric_name: str,
    value: float | None,
    bootstrap_color: str,
    use_custom_class: bool,
    card_id: str | None,
    metric_data: dict[str, Any],
) -> Any:
    """Build performance or WIP badge with tooltip for card header.

    Returns the badge wrapped in a tooltip container, or None if no badge applies.
    """
    badge_element = None
    badge_tooltip_text = None

    if metric_name == "flow_load" and value is not None:
        # WIP-specific badge with dynamic thresholds
        wip_thresholds = metric_data.get("wip_thresholds", {})

        if wip_thresholds and "healthy" in wip_thresholds:
            healthy_threshold = wip_thresholds["healthy"]
            warning_threshold = wip_thresholds["warning"]
            high_threshold = wip_thresholds["high"]
            critical_threshold = wip_thresholds["critical"]

            if value < healthy_threshold:
                badge_text = f"Healthy (<{healthy_threshold:.1f})"
                badge_tooltip_text = (
                    "Optimal WIP - Team capacity is healthy and sustainable"
                )
            elif value < warning_threshold:
                badge_text = f"Warning (<{warning_threshold:.1f})"
                badge_tooltip_text = (
                    "Moderate WIP - Monitor closely, consider finishing "
                    "items before starting new work"
                )
            elif value < high_threshold:
                badge_text = f"High (<{high_threshold:.1f})"
                badge_tooltip_text = (
                    "High WIP - Too much work in progress, implement WIP limits"
                )
            else:
                badge_text = f"Critical (\u2265{critical_threshold:.1f})"
                badge_tooltip_text = (
                    "Critical WIP - Severely overloaded, immediate action required"
                )
        else:
            # Fallback to hardcoded thresholds
            if value < 10:
                badge_text = "Healthy (<10)"
                badge_tooltip_text = (
                    "Optimal WIP - Team capacity is healthy and sustainable"
                )
            elif value < 20:
                badge_text = "Warning (<20)"
                badge_tooltip_text = (
                    "Moderate WIP - Monitor closely, consider finishing "
                    "items before starting new work"
                )
            elif value < 30:
                badge_text = "High (<30)"
                badge_tooltip_text = (
                    "High WIP - Too much work in progress, implement WIP limits"
                )
            else:
                badge_text = "Critical (\u226540)"
                badge_tooltip_text = (
                    "Critical WIP - Severely overloaded, immediate action required"
                )

        badge_id = f"badge-{card_id}" if card_id else f"badge-{metric_name}"
        if use_custom_class:
            badge_element = dbc.Badge(
                children=badge_text,
                className=f"ms-auto bg-{bootstrap_color}",
                style={"fontSize": "0.75rem", "fontWeight": "600"},
                id=badge_id,
            )
        else:
            badge_element = dbc.Badge(
                children=badge_text,
                color=bootstrap_color,
                className="ms-auto",
                style={"fontSize": "0.75rem", "fontWeight": "600"},
                id=badge_id,
            )
    else:
        # Regular performance tier badge for DORA and Flow metrics
        perf_tier = metric_data.get("performance_tier")

        if perf_tier:
            dora_tier_tooltips = {
                "Elite": "Top 10% of teams - world-class performance",
                "High": "Top 25% of teams - strong performance",
                "Medium": "Top 50% of teams - room for improvement",
                "Low": "Below average - needs immediate attention",
            }
            flow_tier_tooltips = {
                "Excellent": "Outstanding throughput - team is highly productive",
                "Good": "Solid throughput - consistent delivery pace",
                "Fair": "Acceptable throughput - room for improvement",
                "Low": "Below target throughput - investigate bottlenecks",
                "Slow": "Items taking too long - reduce cycle time",
            }

            badge_tooltip_text = (
                flow_tier_tooltips.get(perf_tier)
                or dora_tier_tooltips.get(perf_tier)
                or "Performance tier indicator"
            )

            badge_id = f"badge-{card_id}" if card_id else f"badge-{metric_name}"
            if use_custom_class:
                badge_element = dbc.Badge(
                    children=perf_tier,
                    className=f"ms-auto bg-{bootstrap_color}",
                    style={"fontSize": "0.75rem", "fontWeight": "600"},
                    id=badge_id,
                )
            else:
                badge_element = dbc.Badge(
                    children=perf_tier,
                    color=bootstrap_color,
                    className="ms-auto",
                    style={"fontSize": "0.75rem", "fontWeight": "600"},
                    id=badge_id,
                )

    if badge_element and badge_tooltip_text:
        badge_id = f"badge-{card_id}" if card_id else f"badge-{metric_name}"
        return html.Div(
            [
                badge_element,
                dbc.Tooltip(
                    badge_tooltip_text,
                    target=badge_id,
                    placement="top",
                    trigger="click",
                    autohide=True,
                ),
            ],
            className="d-inline-block",
        )

    return badge_element


def _build_blend_section(
    blend_metadata: dict[str, Any] | None,
    weekly_values: list[float],
    forecast_data: Any | None,
) -> html.Div | None:
    """Build the blend metadata display section.

    Returns a Div to append to card_body_children, or None if nothing to show.
    """
    if blend_metadata and blend_metadata.get("is_blended"):
        from data.metrics.blending import format_blend_description

        return html.Div(
            [
                html.Hr(className="my-2"),
                html.Div(
                    [
                        html.I(
                            className="fas fa-chart-line me-1",
                            style={"fontSize": "0.8rem"},
                        ),
                        html.Span(
                            "Current Week (Blended)",
                            className="fw-bold",
                            style={"fontSize": "0.85rem"},
                        ),
                        html.Span(
                            " \U0001f4ca",
                            style={"fontSize": "1rem", "marginLeft": "4px"},
                        ),
                    ],
                    className="text-muted mb-2",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Small("Adjusted Total: ", className="text-muted"),
                                html.Small(
                                    f"{blend_metadata['blended']:.1f}",
                                    className="fw-bold",
                                ),
                            ],
                            className="d-flex justify-content-between mb-1",
                        ),
                        html.Div(
                            [
                                html.Small("Actual So Far: ", className="text-muted"),
                                html.Small(
                                    f"{blend_metadata['actual']:.0f}",
                                    className="text-secondary",
                                ),
                            ],
                            className="d-flex justify-content-between mb-1",
                        ),
                        html.Div(
                            [
                                html.Small("Expected: ", className="text-muted"),
                                html.Small(
                                    f"{blend_metadata['forecast']:.1f}",
                                    className="text-secondary",
                                ),
                            ],
                            className="d-flex justify-content-between mb-1",
                        ),
                    ],
                    className="small",
                    style={
                        "backgroundColor": "#f8f9fa",
                        "padding": "8px",
                        "borderRadius": "4px",
                        "fontSize": "0.8rem",
                    },
                ),
                html.Div(
                    [
                        html.I(className="fas fa-info-circle me-1 text-info"),
                        html.Small(
                            format_blend_description(blend_metadata),
                            className="text-muted fst-italic",
                        ),
                    ],
                    className="mt-2",
                    style={"fontSize": "0.75rem"},
                ),
            ],
            className="mb-3",
        )

    if blend_metadata and not blend_metadata.get("is_blended"):
        day_name = blend_metadata.get("day_name", "Today")
        return html.Div(
            [
                html.Hr(className="my-2"),
                html.Div(
                    [
                        html.I(className="fas fa-check-circle me-2 text-success"),
                        html.Small(
                            f"Using actual data ({day_name})",
                            className="text-muted fst-italic",
                        ),
                    ],
                    className="text-center",
                    style={"fontSize": "0.8rem"},
                ),
            ],
            className="mb-3",
        )

    if forecast_data and not blend_metadata:
        weeks_count = len(weekly_values) if weekly_values else 0
        return html.Div(
            [
                html.Hr(className="my-2"),
                html.Div(
                    [
                        html.I(className="fas fa-info-circle me-2 text-info"),
                        html.Small(
                            f"Blending requires 2+ weeks of data (have {weeks_count})",
                            className="text-muted fst-italic",
                        ),
                    ],
                    className="text-center",
                    style={"fontSize": "0.8rem"},
                ),
            ],
            className="mb-3",
        )

    return None


def _build_sparkline_section(
    metric_name: str,
    weekly_labels: list[str],
    sparkline_values: list[float],
    tier_color: str,
    show_details_button: bool,
) -> html.Div | None:
    """Build the inline sparkline trend section with optional expandable chart.

    Returns a Div to append to card_body_children, or None if insufficient data.
    """
    if not (weekly_labels and sparkline_values and len(weekly_labels) > 1):
        return None

    sparkline_color = {
        "green": "#198754",  # Elite/Excellent (Bootstrap success)
        "blue": "#0dcaf0",  # High/Good (cyan)
        "yellow": "#ffc107",  # Medium/Fair (yellow)
        "orange": "#fd7e14",  # Low/Slow (orange)
        "red": "#dc3545",  # Critical (Bootstrap danger)
    }.get(tier_color, "#6c757d")

    mini_sparkline = _create_mini_bar_sparkline(
        sparkline_values, sparkline_color, height=40
    )
    collapse_id = f"{metric_name}-details-collapse"

    sparkline_section_children: list[Any] = [
        html.Small(
            f"Trend (last {len(sparkline_values)} weeks):",
            className="text-muted d-block mb-1",
        ),
        mini_sparkline,
    ]

    if show_details_button:
        sparkline_section_children.append(
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
            )
        )

    return html.Div(
        [
            html.Hr(className="my-2"),
            html.Div(
                sparkline_section_children,
                className="text-center",
            ),
            dbc.Collapse(
                dbc.CardBody(
                    [
                        html.Div(
                            id=f"{metric_name}-details-chart",
                            className="metric-details-chart",
                        ),
                        html.Div(
                            [
                                html.Small(
                                    "Hover for values \u2022 "
                                    "Double-click to reset zoom",
                                    className="text-muted",
                                )
                            ],
                            className="text-center mt-2",
                        ),
                    ],
                    className="bg-white border-top",
                ),
                id=collapse_id,
                is_open=False,
            )
            if show_details_button
            else html.Div(),
        ],
        className="metric-trend-section",
    )
