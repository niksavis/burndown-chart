"""Sprint Tracker Dropdown Callback

Handles sprint selection changes in the Sprint Tracker tab.
"""

import logging

import dash_bootstrap_components as dbc
from dash import Input, Output, callback, callback_context, html, no_update

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
    [
        Output("sprint-data-container", "children"),
        Output("sprint-selector-dropdown", "value", allow_duplicate=True),
    ],
    Input("sprint-selector-dropdown", "value"),
    Input("points-toggle", "value"),
    prevent_initial_call=True,
)
def update_sprint_selection(selected_sprint: str, show_points_list: list):
    """Update Sprint Tracker when sprint selection or points toggle changes.

    Args:
        selected_sprint: Sprint name/ID selected from dropdown
        show_points_list: Story points toggle state

    Returns:
        Tuple of (updated data container, dropdown value)
    """

    # Log which input triggered this callback
    triggered = callback_context.triggered[0] if callback_context.triggered else None
    trigger_id = triggered["prop_id"].split(".")[0] if triggered else "unknown"
    logger.info(
        "update_sprint_selection TRIGGERED by: "
        f"{trigger_id} (sprint={selected_sprint}, points_toggle={show_points_list})"
    )

    if not selected_sprint:
        return no_update, no_update

    logger.info(f"Sprint selection changed to: {selected_sprint}")

    # Determine if story points should be shown (checklist uses "show" as value)
    show_points = "show" in (show_points_list or [])

    # Return the same sprint value
    # to trigger dependent callbacks (like chart update)
    # This ensures chart updates when points toggle changes, without creating a cascade

    # Re-render the entire sprint tracker with the selected sprint
    # We need to reload data and filter to the selected sprint
    try:
        backend = get_backend()
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            return no_update

        dataset = load_sprint_tracker_dataset(active_profile_id, active_query_id)
        settings = dataset["settings"]
        tracked_issues = dataset["tracked_issues"]
        all_issue_states = dataset["all_issue_states"]
        sprint_field = dataset["sprint_field"]
        sprint_snapshots = dataset["sprint_snapshots"]
        status_changelog = dataset["status_changelog"]

        if not tracked_issues:
            return no_update

        if not sprint_field:
            return no_update

        if not sprint_snapshots:
            return no_update

        if selected_sprint not in sprint_snapshots:
            fallback = select_preferred_sprint(
                sprint_snapshots,
                dataset["sprint_metadata"],
            )
            if not fallback:
                logger.warning(
                    f"Selected sprint {selected_sprint} not found in snapshots"
                )
                return no_update
            selected_sprint = fallback["name"]

        # Get selected sprint data
        sprint_data = sprint_snapshots[selected_sprint]

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

        # Get sprint dates for the selected sprint
        sprint_dates = get_sprint_dates(selected_sprint, tracked_issues, sprint_field)
        sprint_start_date = sprint_dates.get("start_date") if sprint_dates else None
        sprint_end_date = sprint_dates.get("end_date") if sprint_dates else None
        sprint_state = sprint_dates.get("state") if sprint_dates else None

        if sprint_state == "ACTIVE":
            sprint_data = reconcile_active_sprint_membership(
                sprint_data,
                tracked_issues,
                selected_sprint,
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
            tracked_issues,
            sprint_start_date=scope_window_start,
            sprint_end_date=sprint_end_date,
        )
        scope_change_issues = get_sprint_scope_change_issues(
            sprint_data,
            sprint_start_date=scope_window_start,
            sprint_end_date=sprint_end_date,
        )

        # Extract sprint_changes with issue lists for progress bars
        sprint_changes = {
            "added": sprint_data.get("added_issues", []),
            "removed": sprint_data.get("removed_issues", []),
        }

        # Create UI components

        # Build summary card data
        summary_card_data = create_sprint_summary_card(
            progress_data, show_points, flow_wip_statuses
        )

        # Create components
        summary_cards = create_sprint_summary_cards(
            selected_sprint,
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

        # Return only the data container content (not the controls)
        return html.Div(
            [
                summary_cards,
                scope_changes_view,
                html.H5("Issue Progress", className="mt-4 mb-3"),
                progress_bars,
            ]
        ), selected_sprint

    except Exception as e:
        import traceback  # noqa: PLC0415

        logger.error(f"Error updating sprint selection: {e}")
        logger.error(traceback.format_exc())

        return (
            dbc.Alert(
                [
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    html.Strong("Error: "),
                    f"Failed to load sprint data: {str(e)}",
                ],
                color="danger",
                className="m-4",
            ),
            selected_sprint,
        )
