"""Sprint Tracker Dropdown Callback

Handles sprint selection changes in the Sprint Tracker tab.
"""

import logging
from dash import callback, Input, Output, State, html, no_update
import dash_bootstrap_components as dbc

logger = logging.getLogger(__name__)


@callback(
    [
        Output("sprint-data-container", "children"),
        Output("sprint-selector-dropdown", "value", allow_duplicate=True),
    ],
    Input("sprint-selector-dropdown", "value"),
    State("points-toggle", "value"),
    prevent_initial_call=True,
)
def update_sprint_selection(selected_sprint: str, show_points_list: list):
    """Update Sprint Tracker data when user selects a different sprint.

    Args:
        selected_sprint: Sprint name/ID selected from dropdown
        show_points_list: Story points toggle state

    Returns:
        Tuple of (updated data container, dropdown value)
    """
    if not selected_sprint:
        return no_update, no_update

    logger.info(f"Sprint selection changed to: {selected_sprint}")

    # Determine if story points should be shown
    show_points = "points" in (show_points_list or [])

    # Re-render the entire sprint tracker with the selected sprint
    # We need to reload data and filter to the selected sprint
    try:
        from data.persistence.factory import get_backend
        from data.sprint_manager import filter_sprint_issues, get_sprint_snapshots
        from data.persistence import load_app_settings

        backend = get_backend()
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            return no_update

        # Load issues
        all_issues = backend.get_issues(active_profile_id, active_query_id)
        tracked_issues = filter_sprint_issues(all_issues)

        if not tracked_issues:
            return no_update

        # Get sprint field
        settings = load_app_settings()
        field_mappings = settings.get("field_mappings", {})
        general_mappings = field_mappings.get("general", {})
        sprint_field = general_mappings.get("sprint_field")

        if not sprint_field:
            return no_update

        # Load changelog (try both custom field ID and "Sprint" display name)
        changelog_entries = backend.get_changelog_entries(
            active_profile_id, active_query_id, field_name=sprint_field
        )

        if not changelog_entries:
            changelog_entries = backend.get_changelog_entries(
                active_profile_id, active_query_id, field_name="Sprint"
            )

        if not changelog_entries:
            return no_update

        # Build sprint snapshots
        sprint_snapshots = get_sprint_snapshots(tracked_issues, changelog_entries, sprint_field)

        if selected_sprint not in sprint_snapshots:
            logger.warning(f"Selected sprint {selected_sprint} not found in snapshots")
            return no_update

        # Get selected sprint data
        sprint_data = sprint_snapshots[selected_sprint]

        # Calculate progress
        from data.sprint_manager import calculate_sprint_progress, detect_sprint_changes

        flow_end_statuses = settings.get("flow_end_statuses", ["Done", "Closed"])
        flow_wip_statuses = settings.get("wip_statuses", ["In Progress"])

        progress_data = calculate_sprint_progress(
            sprint_data, flow_end_statuses, flow_wip_statuses
        )
        sprint_changes = detect_sprint_changes(changelog_entries)
        selected_sprint_changes = sprint_changes.get(selected_sprint, {})

        # Create UI components
        from ui.sprint_tracker import (
            create_sprint_summary_cards,
            create_sprint_change_indicators,
        )
        from visualization.sprint_charts import (
            create_sprint_progress_bars,
            create_sprint_summary_card,
        )

        # Build summary card data
        summary_card_data = create_sprint_summary_card(
            progress_data, show_points, flow_wip_statuses
        )

        # Create components
        summary_cards = create_sprint_summary_cards(
            selected_sprint, summary_card_data, show_points
        )

        change_indicators = create_sprint_change_indicators(
            len(selected_sprint_changes.get("added", [])),
            len(selected_sprint_changes.get("removed", [])),
            len(selected_sprint_changes.get("moved_in", [])),
            len(selected_sprint_changes.get("moved_out", [])),
        )

        # Load status changelog
        status_changelog = backend.get_changelog_entries(
            active_profile_id, active_query_id, field_name="status"
        )

        # Get sprint dates for the selected sprint
        from data.sprint_manager import get_sprint_dates

        sprint_dates = get_sprint_dates(selected_sprint, tracked_issues, sprint_field)
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
            sprint_state=sprint_state,
        )

        # Return only the data container content (not the controls)
        return html.Div(
            [
                summary_cards,
                change_indicators,
                html.H5("Issue Progress", className="mt-4 mb-3"),
                progress_bars,
            ]
        ), selected_sprint

    except Exception as e:
        import traceback

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
