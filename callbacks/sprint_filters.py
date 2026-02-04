"""Sprint Tracker Filter Callbacks

Handles filtering of sprint data by issue type.
"""

import logging
from dash import callback, Input, Output, State, no_update, html
import dash_bootstrap_components as dbc

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
        from data.persistence.factory import get_backend
        from data.sprint_manager import (
            filter_sprint_issues,
            get_sprint_snapshots,
            calculate_sprint_progress,
            calculate_sprint_scope_changes,
            get_active_sprint_from_issues,
        )
        from data.persistence import load_app_settings
        from ui.sprint_tracker import (
            create_sprint_summary_cards,
            create_no_sprints_state,
        )
        from visualization.sprint_charts import (
            create_sprint_progress_bars,
            create_sprint_summary_card,
        )

        backend = get_backend()
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            return create_no_sprints_state()

        # Load issues and changelog
        all_issues = backend.get_issues(active_profile_id, active_query_id)
        if not all_issues:
            return create_no_sprints_state()

        # CRITICAL: Filter out parent issues dynamically (don't hardcode "Epic")
        settings = load_app_settings()
        parent_field = settings.get("field_mappings", {}).get("general", {}).get("parent_field")
        
        if parent_field:
            from data.parent_filter import filter_parent_issues
            all_issues = filter_parent_issues(
                all_issues,
                parent_field,
                log_prefix="SPRINT FILTERS"
            )

        # Filter to tracked issue types (Story/Task/Bug only)
        if issue_type_filter == "all":
            tracked_types = ["Story", "Task", "Bug"]
        else:
            tracked_types = [issue_type_filter]

        filtered_issues = filter_sprint_issues(
            all_issues, tracked_issue_types=tracked_types
        )

        if not filtered_issues:
            return html.Div(
                [
                    dbc.Alert(
                        [
                            html.I(className="fas fa-filter fa-2x mb-3"),
                            html.H5(f"No {issue_type_filter} Issues Found"),
                            html.P(
                                f"No issues of type '{issue_type_filter}' in current sprint. "
                                "Try selecting 'All' or a different issue type."
                            ),
                        ],
                        color="info",
                        className="text-center p-5",
                    )
                ],
                className="container mt-5",
            )

        # Load sprint changelog
        settings = load_app_settings()
        field_mappings = settings.get("field_mappings", {})
        sprint_field = field_mappings.get("sprint_tracker", {}).get(
            "sprint_field", "customfield_10005"
        )

        sprint_changelog = backend.get_changelog_entries(
            active_profile_id, active_query_id, field_name="Sprint"
        )

        # Build sprint snapshots from filtered issues
        sprint_snapshots = get_sprint_snapshots(
            filtered_issues, sprint_changelog, sprint_field
        )

        if not sprint_snapshots:
            return create_no_sprints_state()

        # Use provided sprint or detect active sprint
        if selected_sprint and selected_sprint in sprint_snapshots:
            selected_sprint_id = selected_sprint
            sprint_start_date = None
            sprint_end_date = None
        else:
            active_sprint_info = get_active_sprint_from_issues(
                filtered_issues, sprint_field
            )
            sprint_ids = sorted(sprint_snapshots.keys(), reverse=True)
            if active_sprint_info and active_sprint_info["name"] in sprint_snapshots:
                selected_sprint_id = active_sprint_info["name"]
                sprint_start_date = active_sprint_info.get("start_date")
                sprint_end_date = active_sprint_info.get("end_date")
            elif sprint_ids:
                selected_sprint_id = sprint_ids[0]
                sprint_start_date = None
                sprint_end_date = None
            else:
                return create_no_sprints_state()

        sprint_data = sprint_snapshots[selected_sprint_id]

        # Debug: Log issue types in sprint data
        issue_states = sprint_data.get("issue_states", {})
        issue_types_in_sprint = set(
            state.get("issue_type") for state in issue_states.values()
        )
        logger.info(
            f"[Filter Debug] Issue types in sprint_data: {issue_types_in_sprint}, Filter: {issue_type_filter}"
        )

        # Calculate sprint progress
        flow_end_statuses = settings.get("flow_end_statuses", ["Done", "Closed"])
        flow_wip_statuses = settings.get("wip_statuses", ["In Progress"])

        progress_data = calculate_sprint_progress(
            sprint_data, flow_end_statuses, flow_wip_statuses
        )

        # Calculate sprint scope changes
        scope_changes = calculate_sprint_scope_changes(sprint_data, None)

        # Extract sprint_changes with issue lists for progress bars
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
            selected_sprint_id, summary_card_data, show_points
        )

        # Load status changelog for timeline
        status_changelog = backend.get_changelog_entries(
            active_profile_id, active_query_id, field_name="status"
        )

        # Get sprint dates for the selected sprint
        from data.sprint_manager import get_sprint_dates

        sprint_dates = get_sprint_dates(
            selected_sprint_id, filtered_issues, sprint_field
        )
        sprint_start_date = sprint_dates.get("start_date") if sprint_dates else None
        sprint_end_date = sprint_dates.get("end_date") if sprint_dates else None
        sprint_state = sprint_dates.get("state") if sprint_dates else None

        # Load flow configuration for dynamic status colors
        from data.persistence import load_app_settings

        app_settings = load_app_settings()
        flow_start_statuses = app_settings.get("flow_start_statuses", [])
        flow_wip_statuses = app_settings.get("wip_statuses", [])
        flow_end_statuses = app_settings.get("flow_end_statuses", [])

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
