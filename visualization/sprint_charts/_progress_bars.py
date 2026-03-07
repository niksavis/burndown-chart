"""Main sprint progress bars orchestrator and sprint header builder."""

import logging
from datetime import UTC, datetime

import dash_bootstrap_components as dbc
from dash import html

from ._bar_multi import _process_issue_bar
from ._bar_single import _create_simple_html_bars
from ._health import _sort_issues_by_health_priority
from ._status import _create_status_legend

logger = logging.getLogger(__name__)


def _build_sprint_progress_info(
    sprint_start: datetime,
    sprint_end: datetime,
    sprint_duration_seconds: float,
    now: datetime,
    sprint_state: str | None,
    scope_changes: dict | None,
    sprint_data: dict,
) -> html.Div:
    """Build the sprint progress header with TODAY indicator and scope change badges.

    Args:
        sprint_start: Sprint start datetime
        sprint_end: Sprint end datetime
        sprint_duration_seconds: Total sprint duration in seconds
        now: Current datetime
        sprint_state: Sprint state (ACTIVE/CLOSED/FUTURE)
        scope_changes: Dict with added/removed/net_change counts
        sprint_data: Full sprint data dict (for issue_states count)

    Returns:
        html.Div with sprint progress header
    """
    elapsed_time = (now - sprint_start).total_seconds()
    time_progress_pct = min(100, (elapsed_time / sprint_duration_seconds) * 100)

    # Determine time text based on sprint state
    if sprint_state == "CLOSED":
        sprint_duration_days = (sprint_end - sprint_start).total_seconds() / 86400
        time_text = f"(Lasted {sprint_duration_days:.1f} days)"
    elif sprint_state == "FUTURE":
        time_text = "(Not started yet)"
    else:
        remaining_days = (sprint_end - now).total_seconds() / 86400
        time_text = f"({remaining_days:.1f} days remaining)"

    sprint_progress_children = [
        html.Div(
            [
                html.Span(
                    f"Sprint Progress: {time_progress_pct:.0f}%",
                    style={
                        "fontSize": "0.9rem",
                        "fontWeight": "600",
                        "color": "#495057",
                        "marginRight": "15px",
                    },
                ),
                html.Span(
                    time_text,
                    style={
                        "fontSize": "0.85rem",
                        "color": "#6c757d",
                    },
                ),
            ],
            style={"marginBottom": "8px"},
        ),
        # Today indicator visual guide
        html.Div(
            [
                html.Div(
                    style={
                        "width": f"{time_progress_pct:.2f}%",
                        "height": "4px",
                        "backgroundColor": "#0d6efd",
                        "borderRadius": "2px",
                        "position": "relative",
                    },
                ),
                html.Div(
                    "TODAY",
                    style={
                        "position": "absolute",
                        "left": f"{time_progress_pct:.2f}%",
                        "top": "-2px",
                        "transform": "translateX(-50%)",
                        "fontSize": "0.7rem",
                        "fontWeight": "700",
                        "color": "#0d6efd",
                        "backgroundColor": "#fff",
                        "padding": "2px 6px",
                        "borderRadius": "3px",
                        "border": "1px solid #0d6efd",
                        "whiteSpace": "nowrap",
                    },
                ),
            ],
            style={
                "width": "100%",
                "height": "20px",
                "backgroundColor": "#e9ecef",
                "borderRadius": "2px",
                "position": "relative",
                "marginBottom": "10px",
            },
        ),
    ]

    # Add scope changes badges if provided
    if scope_changes:
        badges = []
        added_count = scope_changes.get("added", 0)
        removed_count = scope_changes.get("removed", 0)
        net_change = scope_changes.get("net_change", 0)

        # Calculate initial issue count (issues present at sprint start)
        total_issues = len(sprint_data.get("issue_states", {}))
        initial_issues = total_issues - net_change

        if added_count > 0:
            badges.extend(
                [
                    dbc.Tooltip(
                        "Issues added to this sprint after it started "
                        f"({added_count} issues)",
                        target="badge-added-inline",
                        placement="top",
                        trigger="click",
                        autohide=True,
                    ),
                    dbc.Badge(
                        [
                            html.I(className="fas fa-plus me-1"),
                            f"{added_count} Added",
                        ],
                        color="success",
                        className="me-2",
                        id="badge-added-inline",
                    ),
                ]
            )

        if removed_count > 0:
            badges.extend(
                [
                    dbc.Tooltip(
                        "Issues removed from this sprint after it started "
                        f"({removed_count} issues)",
                        target="badge-removed-inline",
                        placement="top",
                        trigger="click",
                        autohide=True,
                    ),
                    dbc.Badge(
                        [
                            html.I(className="fas fa-minus me-1"),
                            f"{removed_count} Removed",
                        ],
                        color="danger",
                        className="me-2",
                        id="badge-removed-inline",
                    ),
                ]
            )

        if net_change != 0:
            net_icon = "fa-arrow-up" if net_change > 0 else "fa-arrow-down"
            net_color = "info" if net_change > 0 else "warning"
            net_sign = "+" if net_change > 0 else ""

            badges.extend(
                [
                    dbc.Tooltip(
                        "Net scope change after sprint start: "
                        f"{net_sign}{net_change} issues (Added - Removed). "
                        "Note: Initial issues present at sprint start "
                        "are not included in this count.",
                        target="badge-net-change-inline",
                        placement="top",
                        trigger="click",
                        autohide=True,
                    ),
                    dbc.Badge(
                        [
                            html.I(className=f"fas {net_icon} me-1"),
                            f"{net_sign}{net_change} Net Change",
                        ],
                        color=net_color,
                        className="me-2",
                        id="badge-net-change-inline",
                    ),
                ]
            )

        if initial_issues > 0:
            badges.extend(
                [
                    dbc.Tooltip(
                        f"{initial_issues} issues were already in the sprint "
                        "when it started. "
                        f"Total issues = {initial_issues} initial + "
                        f"{net_change} net change = {total_issues}",
                        target="badge-initial-inline",
                        placement="top",
                        trigger="click",
                        autohide=True,
                    ),
                    dbc.Badge(
                        [
                            html.I(className="fas fa-circle-dot me-1"),
                            f"{initial_issues} Initial",
                        ],
                        color="secondary",
                        className="me-2",
                        id="badge-initial-inline",
                    ),
                ]
            )

        if badges:
            sprint_progress_children.append(
                html.Div(
                    [
                        html.Span(
                            "Sprint Scope Changes: ",
                            style={
                                "fontSize": "0.85rem",
                                "fontWeight": "600",
                                "color": "#495057",
                                "marginRight": "8px",
                            },
                        ),
                        html.Div(badges, className="d-inline"),
                    ],
                    style={"marginTop": "8px"},
                )
            )

    return html.Div(
        sprint_progress_children,
        style={
            "marginBottom": "15px",
            "padding": "10px",
            "backgroundColor": "#f8f9fa",
            "borderRadius": "4px",
        },
    )


def create_sprint_progress_bars(
    sprint_data: dict,
    changelog_entries: list[dict] | None = None,
    show_points: bool = False,
    sprint_start_date: str | None = None,
    sprint_end_date: str | None = None,
    flow_start_statuses: list[str] | None = None,
    flow_wip_statuses: list[str] | None = None,
    flow_end_statuses: list[str] | None = None,
    sprint_changes: dict | None = None,
    sprint_state: str | None = None,
    scope_changes: dict | None = None,
):
    """Create HTML progress bars showing time proportion spent in each status.

    Each bar represents one issue with colored segments showing the PERCENTAGE
    of time the issue spent in each status (like a pie chart spread horizontally).

    Example: Issue spent 30% in To Do, 50% in Progress, 20% in Done
    Bar shows: [Gray 30%][Blue 50%][Green 20%]

    Args:
        sprint_data: Sprint snapshot from sprint_manager.get_sprint_snapshots()
        changelog_entries: Status change history (REQUIRED for time calculation)
        show_points: Whether to show story points
        sprint_start_date: Sprint start date (ISO format)
        sprint_end_date: Sprint end date (ISO format)
        flow_start_statuses: List of start statuses
        flow_wip_statuses: List of WIP statuses
        flow_end_statuses: List of end statuses
        sprint_changes: Dict with added/removed/moved_in/moved_out issue lists
        sprint_state: Sprint state (ACTIVE/CLOSED/FUTURE)
        scope_changes: Dict with added/removed/net_change counts for badges

    Returns:
        Dash HTML component with styled progress bars
    """
    # Default flow states if not provided or empty
    if not flow_start_statuses:
        flow_start_statuses = ["To Do", "Backlog", "Open"]
    if not flow_wip_statuses:
        flow_wip_statuses = ["In Progress", "In Review", "Testing"]
    if not flow_end_statuses:
        flow_end_statuses = ["Done", "Closed", "Resolved"]

    # Create sets for quick lookup of added/removed issues
    added_issues: set = set()
    removed_issues: set = set()
    if sprint_changes:
        added_issues = {item["issue_key"] for item in sprint_changes.get("added", [])}
        removed_issues = {
            item["issue_key"] for item in sprint_changes.get("removed", [])
        }
    logger.info(
        f"Creating sprint progress bars for: {sprint_data.get('name', 'Unknown')}"
    )

    issue_states = sprint_data.get("issue_states", {})
    if not issue_states:
        return html.Div("No issues in sprint", className="text-muted text-center p-4")

    if not changelog_entries:
        logger.warning("No status changelog - showing current status only")

        # Parse sprint dates even for simple bars
        sprint_start = None
        sprint_end = None
        now = datetime.now(UTC)

        try:
            if sprint_start_date:
                sprint_start = datetime.fromisoformat(sprint_start_date)
                if sprint_start.tzinfo is None:
                    sprint_start = sprint_start.replace(tzinfo=UTC)

            if sprint_end_date:
                sprint_end = datetime.fromisoformat(sprint_end_date)
                if sprint_end.tzinfo is None:
                    sprint_end = sprint_end.replace(tzinfo=UTC)
        except (ValueError, AttributeError) as e:
            logger.error(f"Failed to parse sprint dates: {e}")

        return _create_simple_html_bars(
            issue_states,
            show_points,
            flow_start_statuses,
            flow_wip_statuses,
            flow_end_statuses,
            sprint_start=sprint_start,
            sprint_end=sprint_end,
            now=now,
        )

    # Parse sprint dates to calculate sprint duration
    sprint_duration_seconds = None
    sprint_start = None
    sprint_end = None
    now = datetime.now(UTC)

    try:
        if sprint_start_date:
            sprint_start = datetime.fromisoformat(sprint_start_date)
            if sprint_start.tzinfo is None:
                sprint_start = sprint_start.replace(tzinfo=UTC)

        if sprint_end_date:
            sprint_end = datetime.fromisoformat(sprint_end_date)
            if sprint_end.tzinfo is None:
                sprint_end = sprint_end.replace(tzinfo=UTC)

        # Calculate sprint duration
        if sprint_start and sprint_end:
            sprint_duration_seconds = (sprint_end - sprint_start).total_seconds()
            logger.info(
                "[SPRINT PROGRESS] Sprint duration: "
                f"{sprint_duration_seconds / 86400:.1f} days"
            )
        else:
            logger.warning("Sprint dates not provided - using default 14 days")
            sprint_duration_seconds = 14 * 86400  # Default 14 days

    except (ValueError, AttributeError) as e:
        logger.error(f"Failed to parse sprint dates: {e}")
        sprint_duration_seconds = 14 * 86400  # Default 14 days

    # Build HTML progress bars for each issue sorted by health priority
    issue_keys = _sort_issues_by_health_priority(
        issue_states,
        changelog_entries,
        flow_end_statuses,
        flow_wip_statuses,
        sprint_start_date,
        sprint_end_date,
    )

    logger.info(
        f"[SPRINT PROGRESS] Building progress bars for {len(issue_keys)} issues"
    )
    logger.info(
        f"[SPRINT PROGRESS] Received {len(changelog_entries)} changelog entries"
    )

    progress_bars = []
    all_time_segments = []  # Collect all segments for legend

    for issue_key in issue_keys:
        state = issue_states[issue_key]
        bar, time_segments = _process_issue_bar(
            issue_key,
            state,
            changelog_entries,
            sprint_start,
            sprint_end,
            now,
            sprint_duration_seconds,
            show_points,
            added_issues,
            removed_issues,
            flow_start_statuses,
            flow_wip_statuses,
            flow_end_statuses,
        )
        progress_bars.append(bar)
        all_time_segments.extend(time_segments)

    # Create legend if we have time segments
    legend = None
    if all_time_segments:
        legend = _create_status_legend(
            all_time_segments,
            flow_start_statuses,
            flow_wip_statuses,
            flow_end_statuses,
            changelog_entries,  # Pass changelog for position analysis
        )

    # Add sprint progress indicator
    sprint_progress_info = None
    if sprint_start and sprint_end:
        sprint_progress_info = _build_sprint_progress_info(
            sprint_start,
            sprint_end,
            sprint_duration_seconds,
            now,
            sprint_state,
            scope_changes,
            sprint_data,
        )

    # Return sprint progress + legend + progress bars (title added by callback)
    content = []
    if sprint_progress_info:
        content.append(sprint_progress_info)
    if legend:
        content.append(legend)
    content.extend(progress_bars)
    return html.Div(
        content,
        className="p-3",
    )
