"""Private section builder for the scope indicators row."""

from dash import html

from configuration import SCOPE_HELP_TEXTS
from ui.tooltip_utils import create_info_tooltip

from ._helpers import create_forecast_pill
from ._indicator import create_scope_change_indicator


def _build_scope_indicators_section(
    scope_change_rate: dict,
    threshold: float,
    items_throughput_ratio: float,
    points_throughput_ratio: float,
    total_created_items: float,
    total_completed_items: float,
    total_created_points: float,
    total_completed_points: float,
    threshold_items: int,
    threshold_points: int,
    baseline_items: float,
    baseline_points: float,
    show_points: bool,
) -> html.Div:
    """Build the items + points scope change indicator row."""
    info_icon_class = "fas fa-info-circle text-info ms-2 cursor-pointer"
    points_header_icon_class = "fas fa-chart-bar me-2 text-points"
    calc_icon_class = "fas fa-calculator text-info ms-2 cursor-pointer"
    line_icon_class = "fas fa-chart-line text-info ms-2 cursor-pointer"
    bar_icon_class = "fas fa-chart-bar text-info ms-2 cursor-pointer"
    forecast_pills_class = "d-flex flex-wrap align-items-center mt-2 gap-1"
    points_scope_change_help = (
        SCOPE_HELP_TEXTS["scope_change_rate"]
        + " This version measures scope changes based on story points "
        "rather than item counts."
    )
    points_scope_methodology_help = (
        SCOPE_HELP_TEXTS["scope_metrics_explanation"]
        + " This version tracks changes based on story points rather than "
        "item counts, giving a weighted view of scope complexity changes."
    )
    points_throughput_help = (
        SCOPE_HELP_TEXTS["throughput_ratio"]
        + " Points-based throughput shows if scope complexity is growing "
        "faster than delivery capability."
    )
    items_scope_breakdown_help = (
        "Breakdown of scope metrics: Created items show new work added, "
        "Completed items show work finished, Threshold shows the alert level, "
        "and Baseline shows the initial backlog remaining at the start of "
        "this tracking period (calculated as current remaining + completed "
        "- created in period)."
    )
    points_scope_breakdown_help = (
        "Breakdown of scope metrics based on story points: Created points "
        "show complexity of new work added, Completed points show effort "
        "delivered, Threshold shows the alert level for complexity growth, "
        "and Baseline shows the initial backlog remaining at the start of "
        "this tracking period (calculated as current remaining + completed "
        "- created in period)."
    )
    return html.Div(
        [
            # Items trend box
            html.Div(
                [
                    # Header with icon and tooltip - matching weekly metrics style
                    html.Div(
                        className="d-flex align-items-center mb-2",
                        children=[
                            html.I(className="fas fa-tasks me-2 text-brand"),
                            html.Span(
                                "Scope Change vs Baseline (Items)",
                                className="fw-medium",
                            ),
                            html.I(
                                className=info_icon_class,
                                id="info-tooltip-items-scope-methodology",
                            ),
                        ],
                    ),
                    # Enhanced scope change indicator with tooltips
                    html.Div(
                        [
                            create_scope_change_indicator(
                                "Scope Change vs Baseline (Items)",
                                scope_change_rate["items_rate"],
                                threshold,
                                SCOPE_HELP_TEXTS["scope_change_rate"],
                                items_throughput_ratio,
                            ),
                            # Add scope calculation tooltip icon
                            html.I(
                                className=calc_icon_class,
                                id="info-tooltip-items-scope-calculation",
                            ),
                            # Add throughput ratio tooltip icon
                            html.I(
                                className=line_icon_class,
                                id="info-tooltip-items-throughput-ratio",
                            ),
                            # Add scope breakdown methodology tooltip icon
                            html.I(
                                className=bar_icon_class,
                                id="info-tooltip-items-scope-breakdown",
                            ),
                        ],
                        className="d-flex align-items-center gap-1",
                    ),
                    # Enhanced forecast pills - matching weekly metrics style
                    html.Div(
                        [
                            create_forecast_pill(
                                "Created",
                                f"{int(total_created_items)} items",
                                "brand",
                            ),
                            create_forecast_pill(
                                "Completed",
                                f"{int(total_completed_items)} items",
                                "accent",
                            ),
                            create_forecast_pill(
                                "Threshold",
                                f"{int(threshold_items)} items",
                                "warning",
                            ),
                            html.Div(
                                html.Small(
                                    f"baseline: {int(baseline_items)} items",
                                    className="text-muted fst-italic",
                                ),
                                className="metric-baseline-note",
                            ),
                        ],
                        className=forecast_pills_class,
                    ),
                    # Tooltip components - matching weekly metrics pattern
                    html.Div(
                        [
                            create_info_tooltip(
                                "items-scope-methodology",
                                SCOPE_HELP_TEXTS["scope_metrics_explanation"],
                            ),
                            create_info_tooltip(
                                "items-scope-calculation",
                                SCOPE_HELP_TEXTS["scope_change_rate"],
                            ),
                            create_info_tooltip(
                                "items-throughput-ratio",
                                SCOPE_HELP_TEXTS["throughput_ratio"],
                            ),
                            create_info_tooltip(
                                "items-scope-breakdown",
                                items_scope_breakdown_help,
                            ),
                        ],
                        className="d-none",
                    ),
                ],
                className="col-md-6 col-12 mb-3 pe-md-2",
            ),
            # Points trend box - only show if points tracking is enabled
        ]
        + (
            [
                html.Div(
                    [
                        # Header with icon and tooltip - matching weekly metrics style
                        html.Div(
                            className="d-flex align-items-center mb-2",
                            children=[
                                html.I(className=points_header_icon_class),
                                html.Span(
                                    "Scope Change vs Baseline (Points)",
                                    className="fw-medium",
                                ),
                                html.I(
                                    className=info_icon_class,
                                    id="info-tooltip-points-scope-methodology",
                                ),
                            ],
                        ),
                        # Enhanced scope change indicator with tooltips
                        html.Div(
                            [
                                create_scope_change_indicator(
                                    "Scope Change vs Baseline (Points)",
                                    scope_change_rate["points_rate"],
                                    threshold,
                                    points_scope_change_help,
                                    points_throughput_ratio,
                                ),
                                # Add scope calculation tooltip icon
                                html.I(
                                    className=calc_icon_class,
                                    id="info-tooltip-points-scope-calculation",
                                ),
                                # Add throughput ratio tooltip icon
                                html.I(
                                    className=line_icon_class,
                                    id="info-tooltip-points-throughput-ratio",
                                ),
                                # Add scope breakdown methodology tooltip icon
                                html.I(
                                    className=bar_icon_class,
                                    id="info-tooltip-points-scope-breakdown",
                                ),
                            ],
                            className="d-flex align-items-center gap-1",
                        ),
                        # Enhanced forecast pills - matching weekly metrics style
                        html.Div(
                            [
                                create_forecast_pill(
                                    "Created",
                                    f"{int(total_created_points)} points",
                                    "points",
                                ),
                                create_forecast_pill(
                                    "Completed",
                                    f"{int(total_completed_points)} points",
                                    "accent",
                                ),
                                create_forecast_pill(
                                    "Threshold",
                                    f"{int(threshold_points)} points",
                                    "warning",
                                ),
                                html.Div(
                                    html.Small(
                                        (f"baseline: {int(baseline_points)} points"),
                                        className="text-muted fst-italic",
                                    ),
                                    className="metric-baseline-note",
                                ),
                            ],
                            className=forecast_pills_class,
                        ),
                        # Tooltip components - matching weekly metrics pattern
                        html.Div(
                            [
                                create_info_tooltip(
                                    "points-scope-methodology",
                                    points_scope_methodology_help,
                                ),
                                create_info_tooltip(
                                    "points-scope-calculation",
                                    points_scope_change_help,
                                ),
                                create_info_tooltip(
                                    "points-throughput-ratio",
                                    points_throughput_help,
                                ),
                                create_info_tooltip(
                                    "points-scope-breakdown",
                                    points_scope_breakdown_help,
                                ),
                            ],
                            className="d-none",
                        ),
                    ],
                    className="col-md-6 col-12 mb-3 ps-md-2",
                ),
            ]
            if show_points
            else []
        ),
        className="row mb-3",
    )
