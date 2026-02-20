"""
Budget Cards - Timeline Cards Module

Timeline visualization and forecast alignment components.
Extracted from budget_cards.py as part of architectural refactoring.

Cards:
1. Forecast vs Budget Alignment - PERT forecast vs runway comparison
2. Budget Timeline - Visual project milestone timeline

Note: These functions are large (542 and 844 lines) and violate the 500-line
guideline individually, but extracted together for now. Future refactoring
should decompose these into smaller helper functions.

Created: January 30, 2026 (extracted from budget_cards.py)
"""

import logging
import math
from datetime import datetime, timedelta
from typing import Any

import dash_bootstrap_components as dbc
from dash import html

from ui.styles import create_metric_card_header

logger = logging.getLogger(__name__)


def _create_card_footer(text: str, icon: str = "fa-info-circle") -> dbc.CardFooter:
    """Create consistent card footer with info text.

    DRY helper for uniform card footers across budget and dashboard cards.

    Args:
        text: Footer text to display
        icon: FontAwesome icon class (default: fa-info-circle)

    Returns:
        CardFooter component with consistent styling

    Example:
        >>> footer = _create_card_footer(
        ...     "Based on last 7 weeks | Flow Distribution classification",
        ...     "fa-chart-bar"
        ... )
    """
    return dbc.CardFooter(
        html.Div(
            [
                html.I(className=f"fas {icon} me-1"),
                text,
            ],
            className="text-center text-muted py-2 px-3",
            style={"fontSize": "0.85rem", "lineHeight": "1.4"},
        ),
        className="bg-light border-top",
    )


def create_forecast_alignment_card(
    pert_time_items: float,
    pert_time_points: float | None,
    runway_weeks: float,
    show_points: bool = True,
    last_date: datetime | None = None,
    card_id: str | None = None,
) -> dbc.Card:
    """
    Create Forecast vs Budget Alignment card showing timeline comparison.

    Displays gap between PERT forecast completion time and budget runway
    for both items and points tracking with dates. Styled as table matching Cost Breakdown card.

    Args:
        pert_time_items: PERT forecast days (items-based)
        pert_time_points: PERT forecast days (points-based)
        runway_weeks: Budget runway in weeks
        show_points: Whether points tracking is active
        last_date: Last statistics date for date calculations (defaults to datetime.now())
        card_id: Optional HTML ID for the card

    Returns:
        Dash Bootstrap Card component (full-width table layout)

    Health Status:
        - Healthy (green): Budget runway >= PERT forecast (gap >= 0)
        - Warning (yellow): Gap between -2 and 0 weeks
        - At Risk (red): Budget exhausts >2 weeks before completion
        - No Data (blue): No budget consumption detected

    Example:
        >>> card = create_forecast_alignment_card(105.0, 92.4, 12.5, True)
    """
    from configuration import COLOR_PALETTE

    # Use last_date for date calculations, fall back to datetime.now()
    reference_date = last_date if last_date else datetime.now()

    # Convert days to weeks
    pert_weeks_items = pert_time_items / 7.0
    pert_weeks_points = pert_time_points / 7.0 if pert_time_points else pert_weeks_items

    # Calculate completion dates
    items_completion_date = reference_date + timedelta(days=pert_time_items)
    points_completion_date = (
        reference_date + timedelta(days=pert_time_points)
        if pert_time_points
        else items_completion_date
    )

    # Calculate runway end date
    runway_end_date = reference_date + timedelta(weeks=runway_weeks)

    # Handle infinity runway (no budget consumption)
    if math.isinf(runway_weeks):
        # Show informational message when no consumption data
        return dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.Span(
                            "Forecast vs Budget Alignment",
                            className="metric-card-title",
                        ),
                        " ",
                        html.I(
                            className="fas fa-info-circle text-info",
                            title="Waiting for budget consumption data",
                        ),
                    ],
                ),
                dbc.CardBody(
                    [
                        dbc.Alert(
                            [
                                html.I(className="fas fa-hourglass-start me-2"),
                                html.Strong("No Budget Consumption Data"),
                                html.P(
                                    "Budget tracking will begin once work completion is recorded. "
                                    "The burn rate is calculated from ACTUAL completed work, not just team cost. "
                                    "Complete some items to start tracking budget consumption.",
                                    className="mb-0 mt-2 small",
                                ),
                            ],
                            color="info",
                            className="mb-0",
                        )
                    ]
                ),
            ],
            id=card_id,
            className="metric-card metric-card-large mb-3",
        )

    # Calculate gaps
    gap_items = runway_weeks - pert_weeks_items
    gap_points = runway_weeks - pert_weeks_points

    # Determine overall health (worst case of items/points)
    min_gap = min(gap_items, gap_points) if show_points else gap_items
    if min_gap >= 0:
        overall_health = "Healthy"
        health_color = "#198754"  # green
        health_icon = "fa-check-circle"
    elif min_gap >= -2:
        overall_health = "Warning"
        health_color = "#ffc107"  # yellow
        health_icon = "fa-exclamation-triangle"
    else:
        overall_health = "At Risk"
        health_color = "#dc3545"  # red
        health_icon = "fa-times-circle"

    # Helper to format gap display
    def format_gap(gap: float) -> tuple[str, str, str]:
        if gap >= 0:
            return f"+{gap:.1f} weeks", "#198754", "fa-arrow-up"
        elif gap >= -2:
            return f"{gap:.1f} weeks", "#ffc107", "fa-minus-circle"
        else:
            return f"{gap:.1f} weeks", "#dc3545", "fa-arrow-down"

    gap_items_text, gap_items_color, gap_items_icon = format_gap(gap_items)
    gap_points_text, gap_points_color, gap_points_icon = format_gap(gap_points)

    # Build content using card-based layout instead of table
    content_items = []

    # Items-based section
    content_items.append(
        html.Div(
            [
                # Header row
                html.Div(
                    [
                        html.I(
                            className="fas fa-tasks me-2",
                            style={
                                "color": COLOR_PALETTE["items"],
                                "fontSize": "1.1rem",
                            },
                        ),
                        html.Span(
                            "Items-based",
                            className="fw-bold",
                            style={"fontSize": "1.1rem"},
                        ),
                    ],
                    className="mb-3",
                ),
                # Content row with 3 columns
                html.Div(
                    [
                        # Expected Completion
                        html.Div(
                            [
                                html.Div(
                                    "Expected Completion",
                                    className="text-muted mb-2",
                                    style={"fontSize": "0.85rem", "fontWeight": "600"},
                                ),
                                html.Div(
                                    f"{pert_weeks_items:.1f} weeks",
                                    className="fw-bold",
                                    style={"fontSize": "1.3rem"},
                                ),
                                html.Div(
                                    items_completion_date.strftime("%Y-%m-%d"),
                                    className="text-muted",
                                    style={"fontSize": "0.85rem"},
                                ),
                            ],
                            className="text-center",
                            style={"flex": "1"},
                        ),
                        # Budget Runway
                        html.Div(
                            [
                                html.Div(
                                    "Budget Runway",
                                    className="text-muted mb-2",
                                    style={"fontSize": "0.85rem", "fontWeight": "600"},
                                ),
                                html.Div(
                                    f"{runway_weeks:.1f} weeks",
                                    className="fw-bold",
                                    style={"fontSize": "1.3rem"},
                                ),
                                html.Div(
                                    runway_end_date.strftime("%Y-%m-%d"),
                                    className="text-muted",
                                    style={"fontSize": "0.85rem"},
                                ),
                            ],
                            className="text-center",
                            style={
                                "flex": "1",
                                "borderLeft": "1px solid #dee2e6",
                                "borderRight": "1px solid #dee2e6",
                            },
                        ),
                        # Gap
                        html.Div(
                            [
                                html.Div(
                                    "Gap",
                                    className="text-muted mb-2",
                                    style={"fontSize": "0.85rem", "fontWeight": "600"},
                                ),
                                html.Div(
                                    [
                                        html.I(className=f"fas {gap_items_icon} me-2"),
                                        html.Span(
                                            gap_items_text,
                                            style={"fontWeight": "bold"},
                                        ),
                                    ],
                                    style={
                                        "fontSize": "1.1rem",
                                        "color": gap_items_color,
                                    },
                                ),
                            ],
                            className="text-center",
                            style={"flex": "1"},
                        ),
                    ],
                    className="d-flex align-items-center",
                    style={"gap": "1rem"},
                ),
            ],
            className="p-3",
            style={
                "borderRadius": "0.375rem",
                "border": "1px solid #dee2e6",
                "backgroundColor": "#f8f9fa",
            },
        )
    )

    # Points-based section (conditional rendering)
    # Case 1: Points tracking disabled - show disabled message
    if not show_points:
        content_items.append(
            html.Div(
                [
                    html.Div(
                        [
                            html.I(
                                className="fas fa-toggle-off me-2",
                                style={"color": "#6c757d", "fontSize": "1.1rem"},
                            ),
                            html.Span(
                                "Points-based",
                                className="fw-bold text-muted",
                                style={"fontSize": "1.1rem"},
                            ),
                        ],
                        className="mb-3",
                    ),
                    # Use same d-flex structure as Items-based for consistent height
                    html.Div(
                        [
                            html.I(className="fas fa-toggle-off fa-lg text-secondary"),
                            html.Div(
                                "Points Tracking Disabled",
                                className="fw-bold",
                                style={"fontSize": "1rem", "color": "#6c757d"},
                            ),
                            html.Small(
                                "Enable Points Tracking in Parameters panel to view story points metrics.",
                                className="text-muted",
                                style={"fontSize": "0.85rem"},
                            ),
                        ],
                        className="d-flex align-items-center justify-content-center flex-column",
                        style={"gap": "0.25rem"},
                    ),
                ],
                className="metric-large-panel mt-3",
                style={
                    "borderRadius": "0.375rem",
                    "border": "1px solid #dee2e6",
                    "backgroundColor": "#f8f9fa",
                },
            )
        )
    # Case 2: Points tracking enabled but no points data
    elif pert_time_points is None or pert_time_points == 0:
        content_items.append(
            html.Div(
                [
                    html.Div(
                        [
                            html.I(
                                className="fas fa-chart-bar me-2",
                                style={"color": "#6c757d", "fontSize": "1.1rem"},
                            ),
                            html.Span(
                                "Points-based",
                                className="fw-bold text-muted",
                                style={"fontSize": "1.1rem"},
                            ),
                        ],
                        className="mb-3",
                    ),
                    # Use same d-flex structure as Items-based for consistent height
                    html.Div(
                        [
                            html.I(className="fas fa-database fa-lg text-secondary"),
                            html.Div(
                                "No Points Data",
                                className="fw-bold",
                                style={"fontSize": "1rem", "color": "#6c757d"},
                            ),
                            html.Small(
                                "No story points data available. Configure story points field in Settings or complete items with point estimates.",
                                className="text-muted",
                                style={"fontSize": "0.85rem"},
                            ),
                        ],
                        className="d-flex align-items-center justify-content-center flex-column",
                        style={"gap": "0.25rem"},
                    ),
                ],
                className="p-3 mt-3",
                style={
                    "borderRadius": "0.375rem",
                    "border": "1px solid #dee2e6",
                    "backgroundColor": "#f8f9fa",
                },
            )
        )
    # Case 3: Points tracking enabled with data - show normal section
    else:
        content_items.append(
            html.Div(
                [
                    # Header row
                    html.Div(
                        [
                            html.I(
                                className="fas fa-chart-bar me-2",
                                style={
                                    "color": COLOR_PALETTE["points"],
                                    "fontSize": "1.1rem",
                                },
                            ),
                            html.Span(
                                "Points-based",
                                className="fw-bold",
                                style={"fontSize": "1.1rem"},
                            ),
                        ],
                        className="mb-3",
                    ),
                    # Content row with 3 columns
                    html.Div(
                        [
                            # Expected Completion
                            html.Div(
                                [
                                    html.Div(
                                        "Expected Completion",
                                        className="text-muted mb-2",
                                        style={
                                            "fontSize": "0.85rem",
                                            "fontWeight": "600",
                                        },
                                    ),
                                    html.Div(
                                        f"{pert_weeks_points:.1f} weeks",
                                        className="fw-bold",
                                        style={"fontSize": "1.3rem"},
                                    ),
                                    html.Div(
                                        points_completion_date.strftime("%Y-%m-%d"),
                                        className="text-muted",
                                        style={"fontSize": "0.85rem"},
                                    ),
                                ],
                                className="text-center",
                                style={"flex": "1"},
                            ),
                            # Budget Runway
                            html.Div(
                                [
                                    html.Div(
                                        "Budget Runway",
                                        className="text-muted mb-2",
                                        style={
                                            "fontSize": "0.85rem",
                                            "fontWeight": "600",
                                        },
                                    ),
                                    html.Div(
                                        f"{runway_weeks:.1f} weeks",
                                        className="fw-bold",
                                        style={"fontSize": "1.3rem"},
                                    ),
                                    html.Div(
                                        runway_end_date.strftime("%Y-%m-%d"),
                                        className="text-muted",
                                        style={"fontSize": "0.85rem"},
                                    ),
                                ],
                                className="text-center",
                                style={
                                    "flex": "1",
                                    "borderLeft": "1px solid #dee2e6",
                                    "borderRight": "1px solid #dee2e6",
                                },
                            ),
                            # Gap
                            html.Div(
                                [
                                    html.Div(
                                        "Gap",
                                        className="text-muted mb-2",
                                        style={
                                            "fontSize": "0.85rem",
                                            "fontWeight": "600",
                                        },
                                    ),
                                    html.Div(
                                        [
                                            html.I(
                                                className=f"fas {gap_points_icon} me-2"
                                            ),
                                            html.Span(
                                                gap_points_text,
                                                style={"fontWeight": "bold"},
                                            ),
                                        ],
                                        style={
                                            "fontSize": "1.1rem",
                                            "color": gap_points_color,
                                        },
                                    ),
                                ],
                                className="text-center",
                                style={"flex": "1"},
                            ),
                        ],
                        className="d-flex align-items-center",
                        style={"gap": "1rem"},
                    ),
                ],
                className="p-3 mt-3",
                style={
                    "borderRadius": "0.375rem",
                    "border": "1px solid #dee2e6",
                    "backgroundColor": "#f8f9fa",
                },
            )
        )

    # Create card with health status badge
    card = dbc.Card(
        [
            create_metric_card_header(
                title="Forecast vs Budget Alignment",
                tooltip_text="Compares PERT forecast completion time with budget runway. "
                "Positive gap = budget outlasts forecast (healthy). "
                "Negative gap = budget exhausts before completion (risk). "
                "Budget runway is calculated from ACTUAL work completed, not just team cost.",
                tooltip_id="metric-forecast_alignment",
                badge=dbc.Badge(
                    overall_health,
                    className="badge",
                    style={
                        "backgroundColor": health_color,
                        "color": "white",
                        "fontSize": "0.85rem",
                        "padding": "0.35rem 0.65rem",
                    },
                ),
            ),
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className=f"fas {health_icon} me-2",
                                        style={"color": health_color},
                                    ),
                                    html.Span(
                                        overall_health,
                                        style={
                                            "color": health_color,
                                            "fontWeight": "bold",
                                            "fontSize": "1.5rem",
                                        },
                                    ),
                                ],
                                className="d-flex align-items-center justify-content-center mb-1",
                            ),
                            html.P(
                                f"Worst gap: {min_gap:+.1f} weeks",
                                className="text-muted mb-3",
                                style={"fontSize": "0.9rem"},
                            ),
                        ],
                        className="text-center",
                    ),
                    html.Div(content_items),
                ],
                className="pt-3 pb-0 mb-0",
            ),
            _create_card_footer(
                "Positive gap = sufficient budget • Negative gap = budget risk • Runway from actual burn rate",
                "fa-balance-scale",
            ),
        ],
        id=card_id,
        className="metric-card metric-card-large mb-3 h-100",
    )

    return card


def create_budget_timeline_card(
    baseline_data: dict[str, Any],
    pert_forecast_weeks: float | None = None,
    last_date: datetime | None = None,
    card_id: str | None = None,
) -> dbc.Card:
    """
    Create Budget Timeline card showing key project dates.

    Displays timeline milestones in a clear table format:
    - Start date, current date, baseline end, forecast, runway end
    - Shows time elapsed and remaining for each milestone
    - Color-coded status indicators

    Args:
        baseline_data: Dict from get_budget_baseline_vs_actual()
        pert_forecast_weeks: Optional PERT forecast weeks for completion date
        last_date: Optional last statistics date for forecast alignment (defaults to datetime.now())
        card_id: Optional HTML ID for the card

    Returns:
        Dash Bootstrap Card component

    Example:
        >>> card = create_budget_timeline_card(baseline_data, 15.0, last_date=datetime(2026, 1, 6))
    """
    # Extract data
    start_date_str = baseline_data["baseline"]["start_date"]
    allocated_end_str = baseline_data["baseline"]["allocated_end_date"]
    runway_end_str = baseline_data["actual"]["runway_end_date"]
    elapsed_weeks = baseline_data["actual"]["elapsed_weeks"]
    allocated_weeks = baseline_data["baseline"]["time_allocated_weeks"]
    runway_vs_baseline_weeks = baseline_data["variance"]["runway_vs_baseline_weeks"]

    # Parse dates
    try:
        # Validate required date strings
        if not start_date_str or not allocated_end_str:
            logger.error(
                f"Missing required timeline dates: start_date='{start_date_str}', allocated_end='{allocated_end_str}'"
            )
            raise ValueError("Missing required timeline dates")

        start_date = datetime.fromisoformat(start_date_str)
        allocated_end = datetime.fromisoformat(allocated_end_str)
        current_date = datetime.now()

        # Parse runway end
        if runway_end_str and runway_end_str not in [
            "N/A (no consumption)",
            "Over budget",
        ]:
            runway_end = datetime.fromisoformat(runway_end_str)
        else:
            runway_end = None

    except Exception as e:
        logger.error(f"Failed to parse timeline dates: {e}")
        return dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Budget Timeline", className="card-title"),
                    html.P(
                        "Unable to calculate timeline dates", className="text-muted"
                    ),
                ]
            ),
            id=card_id,
            className="metric-card mb-3 h-100",
        )

    # Calculate time metrics
    baseline_weeks_remaining = (allocated_end - current_date).days / 7.0

    # Build visual timeline
    # Collect all dates with their metadata
    timeline_markers = [
        {
            "date": start_date,
            "label": "Budget Start",
            "color": "#6610f2",
            "icon": "fa-play",
        },
        {
            "date": current_date,
            "label": "Today",
            "color": "#6f42c1",
            "icon": "fa-calendar-day",
        },
        {
            "date": allocated_end,
            "label": "Baseline End",
            "color": "#d4a017",
            "icon": "fa-flag-checkered",
        },
    ]

    if runway_end:
        runway_color = "#20c997" if runway_vs_baseline_weeks >= 0 else "#e83e8c"
        timeline_markers.append(
            {
                "date": runway_end,
                "label": "Runway End",
                "color": runway_color,
                "icon": "fa-money-bill-wave",
            }
        )

    # Sort by date and find range
    timeline_markers.sort(key=lambda x: x["date"])
    min_date = timeline_markers[0]["date"]
    max_date = timeline_markers[-1]["date"]
    date_range = (max_date - min_date).days

    # Calculate initial positions based on actual dates
    if date_range > 0:
        # Calculate raw positions
        for marker in timeline_markers:
            days_from_start = (marker["date"] - min_date).days
            marker["raw_position"] = (days_from_start / date_range) * 100
    else:
        # All dates are the same - distribute evenly
        spacing = 100 / (len(timeline_markers) + 1)
        for i, marker in enumerate(timeline_markers):
            marker["raw_position"] = spacing * (i + 1)

    # Apply collision detection and adjustment
    # Minimum spacing needed (percentage) to prevent label overlap
    min_spacing = 12  # Approximately 12% of timeline width

    adjusted_positions = []
    for i, marker in enumerate(timeline_markers):
        if i == 0:
            # First marker - ensure it's not too close to edge
            pos = max(8, marker["raw_position"])
        else:
            # Ensure minimum spacing from previous marker
            prev_pos = adjusted_positions[-1]
            desired_pos = marker["raw_position"]

            if desired_pos - prev_pos < min_spacing:
                # Too close - push it out
                pos = prev_pos + min_spacing
            else:
                pos = desired_pos

        adjusted_positions.append(pos)
        marker["position"] = pos

    # Check if any markers overflow past the right edge (92%)
    # If so, redistribute all markers evenly to prevent overlap
    if any(pos > 92 for pos in adjusted_positions):
        # Redistribute evenly across available space
        spacing = 84 / (len(timeline_markers) + 1)  # 84% = 92% - 8% (margins)
        for i, marker in enumerate(timeline_markers):
            marker["position"] = 8 + spacing * (i + 1)
    else:
        # Apply right edge constraint
        for _i, marker in enumerate(timeline_markers):
            marker["position"] = min(marker["position"], 92)

    # Calculate positions (0-100%)
    def calc_position(date):
        # This function is now only used as fallback
        if date_range > 0:
            days_from_start = (date - min_date).days
            return (days_from_start / date_range) * 100
        return 50

    # Build timeline visualization
    timeline_visual = html.Div(
        [
            # Timeline bar with lower z-index
            html.Div(
                style={
                    "position": "absolute",
                    "top": "30px",
                    "left": "30px",
                    "right": "30px",
                    "height": "4px",
                    "backgroundColor": "#e9ecef",
                    "borderRadius": "2px",
                    "zIndex": "1",
                }
            ),
            # Markers overlaying the timeline
            html.Div(
                [
                    html.Div(
                        [
                            # Label overlapping timeline (above)
                            html.Div(
                                marker["label"],
                                style={
                                    "position": "absolute",
                                    "top": "10px",
                                    "left": "50%",
                                    "transform": "translateX(-50%)",
                                    "fontSize": "0.75rem",
                                    "fontWeight": "600",
                                    "color": marker["color"],
                                    "whiteSpace": "nowrap",
                                    "zIndex": "3",
                                },
                            ),
                            # Dot on timeline
                            html.Div(
                                style={
                                    "position": "absolute",
                                    "top": "29px",
                                    "left": "50%",
                                    "transform": "translateX(-50%)",
                                    "width": "8px",
                                    "height": "8px",
                                    "borderRadius": "50%",
                                    "backgroundColor": marker["color"],
                                    "border": "2px solid white",
                                    "zIndex": "3",
                                }
                            ),
                            # Icon below timeline
                            html.Div(
                                html.I(
                                    className=f"fas {marker['icon']}",
                                    style={"fontSize": "0.85rem"},
                                ),
                                style={
                                    "position": "absolute",
                                    "top": "36px",
                                    "left": "50%",
                                    "transform": "translateX(-50%)",
                                    "color": marker["color"],
                                    "zIndex": "3",
                                },
                            ),
                            # Date at bottom (below icon)
                            html.Div(
                                marker["date"].strftime("%Y-%m-%d"),
                                style={
                                    "position": "absolute",
                                    "top": "55px",
                                    "left": "50%",
                                    "transform": "translateX(-50%)",
                                    "fontSize": "0.7rem",
                                    "color": "#6c757d",
                                    "whiteSpace": "nowrap",
                                    "zIndex": "3",
                                },
                            ),
                        ],
                        style={
                            "position": "absolute",
                            "left": f"{marker['position']}%",
                            "top": "0",
                            "height": "100%",
                        },
                    )
                    for marker in timeline_markers
                ],
                style={
                    "position": "absolute",
                    "top": "0",
                    "left": "0",
                    "right": "0",
                    "height": "100%",
                },
            ),
        ],
        style={
            "position": "relative",
            "height": "90px",
            "margin": "20px 0",
        },
    )

    # Build timeline table rows
    timeline_rows = [
        html.Tr(
            [
                html.Td(
                    [
                        html.I(
                            className="fas fa-play me-2", style={"color": "#6610f2"}
                        ),
                        "Budget Start",
                    ],
                    style={"width": "40%"},
                ),
                html.Td(start_date.strftime("%Y-%m-%d"), className="fw-bold"),
                html.Td(
                    f"{allocated_weeks:.0f} weeks allocated",
                    className="text-muted text-end",
                ),
            ]
        ),
        html.Tr(
            [
                html.Td(
                    [
                        html.I(
                            className="fas fa-calendar-day me-2",
                            style={"color": "#6f42c1"},
                        ),
                        "Today",
                    ]
                ),
                html.Td(
                    current_date.strftime("%Y-%m-%d"),
                    className="fw-bold",
                    style={"color": "#6f42c1"},
                ),
                html.Td(
                    f"{elapsed_weeks:.1f} weeks elapsed",
                    className="text-muted text-end",
                ),
            ],
            className="table-active",
        ),
        html.Tr(
            [
                html.Td(
                    [
                        html.I(
                            className="fas fa-flag-checkered me-2",
                            style={"color": "#d4a017"},
                        ),
                        "Baseline End",
                    ]
                ),
                html.Td(allocated_end.strftime("%Y-%m-%d"), className="fw-bold"),
                html.Td(
                    f"{abs(baseline_weeks_remaining):.1f} weeks {'remaining' if baseline_weeks_remaining > 0 else 'overdue'}",
                    className="text-end",
                    style={
                        "color": "#198754"
                        if baseline_weeks_remaining > 0
                        else "#dc3545"
                    },
                ),
            ]
        ),
    ]

    # Add runway row if available
    if runway_end:
        runway_color = "#20c997" if runway_vs_baseline_weeks >= 0 else "#e83e8c"
        runway_text_color = "#198754" if runway_vs_baseline_weeks >= 0 else "#dc3545"
        timeline_rows.append(
            html.Tr(
                [
                    html.Td(
                        [
                            html.I(
                                className="fas fa-money-bill-wave me-2",
                                style={"color": runway_color},
                            ),
                            "Runway End",
                        ]
                    ),
                    html.Td(
                        runway_end.strftime("%Y-%m-%d"),
                        className="fw-bold",
                        style={"color": runway_text_color},
                    ),
                    html.Td(
                        f"{runway_vs_baseline_weeks:+.1f} weeks vs baseline",
                        className="text-end",
                        style={"color": runway_text_color},
                    ),
                ],
                style={"borderTop": "2px solid #dee2e6"},
            )
        )
    elif runway_end_str:
        timeline_rows.append(
            html.Tr(
                [
                    html.Td(
                        [
                            html.I(
                                className="fas fa-money-bill-wave text-secondary me-2"
                            ),
                            "Runway End",
                        ]
                    ),
                    html.Td(
                        runway_end_str,
                        className="text-secondary",
                        colSpan=2,
                        style={"fontStyle": "italic"},
                    ),
                ],
                style={"borderTop": "2px solid #dee2e6"},
            )
        )

    timeline_table = dbc.Table(
        html.Tbody(timeline_rows),
        bordered=False,
        hover=True,
        size="sm",
        className="mb-0",
    )

    # Build card
    card = dbc.Card(
        [
            create_metric_card_header(title="Budget Timeline"),
            dbc.CardBody(
                [timeline_visual, html.Hr(className="my-3"), timeline_table],
                className="p-3",
            ),
            _create_card_footer(
                "Key project milestones • Colors indicate schedule health",
                "fa-clock",
            ),
        ],
        id=card_id,
        className="metric-card metric-card-large mb-3 h-100",
    )

    return card
