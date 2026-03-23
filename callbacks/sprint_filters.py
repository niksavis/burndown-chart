"""Sprint Tracker Filter Callbacks

Handles filtering of sprint data by issue type.
"""

import logging

import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, html, no_update

from data.persistence.factory import get_backend
from data.sprint_manager import (
    calculate_sprint_progress,
    calculate_sprint_scope_change_points,
    calculate_sprint_scope_changes,
    get_sprint_dates,
    get_sprint_scope_change_issues,
    reconcile_active_sprint_membership,
    select_preferred_sprint,
)
from data.sprint_tracker_data import load_sprint_tracker_dataset
from ui.empty_states import create_no_sprints_state
from ui.sprint_tracker import (
    create_sprint_scope_changes_view,
    create_sprint_summary_cards,
)
from visualization.sprint_charts import (
    create_sprint_progress_bars,
    create_sprint_summary_card,
)

logger = logging.getLogger(__name__)


@callback(
    Output("sprint-data-container", "children", allow_duplicate=True),
    Input("sprint-issue-type-filter", "value"),
    State("sprint-selector-dropdown", "value"),
    State("points-toggle", "value"),
    prevent_initial_call=True,
)
def filter_sprint_by_issue_type(
    issue_type_filter: str, selected_sprint: str, show_points_list: list
):
    """Filter Sprint Tracker by issue type.

    Args:
        issue_type_filter: Issue type selected ("all", "Story", "Task", "Bug")
        selected_sprint: Currently selected sprint name
        show_points_list: Story points toggle state

    Returns:
        Updated sprint data container filtered by issue type
    """
    if not issue_type_filter:
        return no_update

    logger.info(f"Filtering sprint by issue type: {issue_type_filter}")

    try:
        backend = get_backend()
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            return create_no_sprints_state()

        dataset = load_sprint_tracker_dataset(
            active_profile_id,
            active_query_id,
            issue_type_filter=issue_type_filter,
        )

        filtered_issues = dataset["tracked_issues"]
        all_issue_states = dataset["all_issue_states"]
        settings = dataset["settings"]
        sprint_field = dataset["sprint_field"]
        sprint_snapshots = dataset["sprint_snapshots"]
        status_changelog = dataset["status_changelog"]

        if not filtered_issues:
            if issue_type_filter != "all":
                return html.Div(
                    [
                        dbc.Alert(
                            [
                                html.I(className="fas fa-filter fa-2x mb-3"),
                                html.H5(f"No {issue_type_filter} Issues Found"),
                                html.P(
                                    f"No issues of type '{issue_type_filter}' "
                                    "in current sprint. "
                                    "Try selecting 'All' or a different issue type."
                                ),
                            ],
                            color="info",
                            className="text-center p-5",
                        )
                    ],
                    className="container mt-5",
                )
            return create_no_sprints_state()

        if not sprint_field:
            logger.warning("Sprint field not configured in field_mappings.general")
            return create_no_sprints_state()

        if not sprint_snapshots:
            return create_no_sprints_state()

        # Use provided sprint or detect active sprint
        if selected_sprint and selected_sprint in sprint_snapshots:
            selected_sprint_id = selected_sprint
            sprint_start_date = None
            sprint_end_date = None
        else:
            selected_info = select_preferred_sprint(
                sprint_snapshots,
                dataset["sprint_metadata"],
            )
            if not selected_info:
                return create_no_sprints_state()
            selected_sprint_id = selected_info["name"]
            sprint_start_date = selected_info.get("start_date")
            sprint_end_date = selected_info.get("end_date")

        sprint_data = sprint_snapshots[selected_sprint_id]

        # Debug: Log issue types in sprint data
        issue_states = sprint_data.get("issue_states", {})
        issue_types_in_sprint = set(
            state.get("issue_type") for state in issue_states.values()
        )
        logger.info(
            "[Filter Debug] Issue types in sprint_data: "
            f"{issue_types_in_sprint}, Filter: {issue_type_filter}"
        )

        # Load flow status configuration - same lists used for metrics and visualization
        flow_start_statuses = settings.get("flow_start_statuses", [])
        flow_wip_statuses = settings.get("wip_statuses", [])
        flow_end_statuses = settings.get("flow_end_statuses", [])
        if not flow_start_statuses:
            flow_start_statuses = ["To Do", "Backlog", "Open"]
        if not flow_wip_statuses:
            flow_wip_statuses = ["In Progress", "In Review", "Testing"]
        if not flow_end_statuses:
            flow_end_statuses = ["Done", "Closed", "Resolved"]

        sprint_dates = get_sprint_dates(
            selected_sprint_id, filtered_issues, sprint_field
        )
        sprint_start_date = sprint_dates.get("start_date") if sprint_dates else None
        sprint_end_date = sprint_dates.get("end_date") if sprint_dates else None
        sprint_state = sprint_dates.get("state") if sprint_dates else None

        if sprint_state == "ACTIVE":
            sprint_data = reconcile_active_sprint_membership(
                sprint_data,
                filtered_issues,
                selected_sprint_id,
                sprint_field,
            )

        scope_window_start = None if sprint_state == "FUTURE" else sprint_start_date

        progress_data = calculate_sprint_progress(
            sprint_data, flow_end_statuses, flow_wip_statuses
        )

        # Calculate sprint scope changes
        scope_changes = calculate_sprint_scope_changes(sprint_data, scope_window_start)
        scope_change_points = calculate_sprint_scope_change_points(
            sprint_data,
            filtered_issues,
            sprint_start_date=scope_window_start,
            sprint_end_date=sprint_end_date,
        )
        scope_change_issues = get_sprint_scope_change_issues(
            sprint_data,
            sprint_start_date=scope_window_start,
            sprint_end_date=sprint_end_date,
        )

        # Extract sprint_changes with issue lists
        # for progress bars
        sprint_changes = {
            "added": sprint_data.get("added_issues", []),
            "removed": sprint_data.get("removed_issues", []),
        }

        # Determine if story points should be shown (checklist uses "show" as value)
        show_points = "show" in (show_points_list or [])

        # Build summary card data
        summary_card_data = create_sprint_summary_card(
            progress_data, show_points, flow_wip_statuses
        )

        # Create UI components
        summary_cards = create_sprint_summary_cards(
            selected_sprint_id,
            summary_card_data,
            show_points,
            scope_change_summary={
                "added_after_start": scope_changes.get("added", 0),
                "removed_after_start": scope_changes.get("removed", 0),
                "added_points_after_start": scope_change_points.get(
                    "added_points", 0.0
                ),
                "removed_points_after_start": scope_change_points.get(
                    "removed_points", 0.0
                ),
            },
            sprint_state=sprint_state,
        )
        scope_changes_view = create_sprint_scope_changes_view(
            scope_change_issues,
            sprint_state=sprint_state,
            issue_states=all_issue_states,
        )

        # Create visualizations
        progress_bars = create_sprint_progress_bars(
            sprint_data,
            status_changelog,
            show_points,
            sprint_start_date=sprint_start_date,
            sprint_end_date=sprint_end_date,
            flow_start_statuses=flow_start_statuses,
            flow_wip_statuses=flow_wip_statuses,
            flow_end_statuses=flow_end_statuses,
            sprint_changes=sprint_changes,  # Pass issue lists for icon indicators
            sprint_state=sprint_state,
            scope_changes=scope_changes,  # Pass scope changes for inline badges
        )

        # Return only data container content (not the controls)
        return html.Div(
            [
                summary_cards,
                scope_changes_view,
                html.H5("Issue Progress", className="mt-4 mb-3"),
                progress_bars,
            ]
        )

    except Exception as e:
        logger.error(f"Error filtering sprint by issue type: {e}", exc_info=True)
        return dbc.Alert(
            [
                html.H5("Error Filtering Sprint"),
                html.P(f"An error occurred while filtering the sprint: {str(e)}"),
            ],
            color="danger",
            className="m-4",
        )
