"""Sprint Tracker Callbacks Module

This module provides callback functions for the Sprint Tracker feature,
handling sprint data rendering and filtering.

Follows Bug Analysis pattern for conditional tab display.
"""

import logging
from typing import Dict
from dash import html
import dash_bootstrap_components as dbc

logger = logging.getLogger(__name__)


def _apply_sprint_filters(
    sprint_data: Dict, issue_type_filter: str = "all", status_filter: str = "all"
) -> Dict:
    """Apply filters to sprint data.

    Args:
        sprint_data: Sprint snapshot from get_sprint_snapshots()
        issue_type_filter: Issue type to filter ("all", "Story", "Task", "Bug")
        status_filter: Status to filter ("all", or specific status)

    Returns:
        Filtered sprint data
    """
    if issue_type_filter == "all" and status_filter == "all":
        return sprint_data

    # Create filtered copy
    filtered_data = {
        "name": sprint_data.get("name"),
        "current_issues": [],
        "added_issues": sprint_data.get("added_issues", []),
        "removed_issues": sprint_data.get("removed_issues", []),
        "issue_states": {},
    }

    # Filter issue_states
    issue_states = sprint_data.get("issue_states", {})
    for issue_key, state in issue_states.items():
        # Apply issue type filter
        if issue_type_filter != "all":
            if state.get("issue_type") != issue_type_filter:
                continue

        # Apply status filter
        if status_filter != "all":
            if state.get("status") != status_filter:
                continue

        # Issue passes filters
        filtered_data["issue_states"][issue_key] = state
        filtered_data["current_issues"].append(issue_key)

    return filtered_data


def _render_sprint_tracker_content(
    data_points_count: int, show_points: bool = False
) -> html.Div:
    """Render Sprint Tracker tab content.

    This is called directly from the main visualization callback for instant
    rendering without loading placeholder.

    Args:
        data_points_count: Number of weeks to include (from timeline filter)
        show_points: Whether to show story points metrics

    Returns:
        Complete Sprint Tracker tab content (html.Div)
    """
    logger.info(
        f"Rendering Sprint Tracker content with data_points: {data_points_count}"
    )

    try:
        # Load issues and changelog from database
        from data.persistence.factory import get_backend

        backend = get_backend()
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            logger.warning("No active profile/query configured")
            from ui.sprint_tracker import create_no_sprints_state

            return create_no_sprints_state()

        # Load issues from database
        all_issues = backend.get_issues(active_profile_id, active_query_id)

        if not all_issues:
            logger.warning("No issues found in database")
            from ui.sprint_tracker import create_no_sprints_state

            return create_no_sprints_state()

        logger.info(f"Loaded {len(all_issues)} issues from database")

        # Filter to tracked issue types (Story, Task, Bug - exclude sub-tasks)
        from data.sprint_manager import filter_sprint_issues

        tracked_issues = filter_sprint_issues(all_issues)

        if not tracked_issues:
            logger.warning("No tracked issue types (Story/Task/Bug) found")
            from ui.sprint_tracker import create_no_sprints_state

            return create_no_sprints_state()

        # Get configured sprint field from settings
        from data.persistence import load_app_settings

        settings = load_app_settings()
        field_mappings = settings.get("field_mappings", {})

        # Sprint field is in general mappings (saved by field mapping UI)
        general_mappings = field_mappings.get("general", {})
        sprint_field = general_mappings.get("sprint_field")

        if not sprint_field:
            logger.warning("Sprint field not configured in field mappings")
            from ui.sprint_tracker import create_no_sprints_state

            return create_no_sprints_state()

        logger.info(f"Using sprint field: {sprint_field}")

        # Load sprint changelog entries using configured sprint field
        # Try both custom field ID and "Sprint" display name (JIRA uses display name in changelog)
        changelog_entries = backend.get_changelog_entries(
            active_profile_id, active_query_id, field_name=sprint_field
        )

        # If no entries with custom field ID, try "Sprint" display name
        if not changelog_entries:
            changelog_entries = backend.get_changelog_entries(
                active_profile_id, active_query_id, field_name="Sprint"
            )
            if changelog_entries:
                logger.info(
                    f"Found {len(changelog_entries)} sprint entries using 'Sprint' field name"
                )

        if not changelog_entries or len(changelog_entries) == 0:
            logger.info("No sprint changelog data found - sprints not configured")
            from ui.sprint_tracker import create_no_sprints_state

            return create_no_sprints_state()

        logger.info(f"Loaded {len(changelog_entries)} sprint changelog entries")

        # Build sprint snapshots from changelog
        from data.sprint_manager import get_sprint_snapshots, detect_sprint_changes

        sprint_snapshots = get_sprint_snapshots(tracked_issues, changelog_entries)

        if not sprint_snapshots:
            logger.warning("No sprint snapshots built from changelog")
            from ui.sprint_tracker import create_no_sprints_state

            return create_no_sprints_state()

        logger.info(f"Built {len(sprint_snapshots)} sprint snapshots")

        # Determine active sprint from issue data (uses JIRA state field)
        from data.sprint_manager import get_active_sprint_from_issues

        active_sprint_info = get_active_sprint_from_issues(tracked_issues, sprint_field)

        # Select active sprint if found, otherwise use first sprint
        sprint_ids = sorted(
            sprint_snapshots.keys(), reverse=True
        )  # Newest first by name
        if active_sprint_info and active_sprint_info["name"] in sprint_snapshots:
            selected_sprint_id = active_sprint_info["name"]
            sprint_start_date = active_sprint_info.get("start_date")
            sprint_end_date = active_sprint_info.get("end_date")
            logger.info(f"Selected active sprint: {selected_sprint_id}")
        elif sprint_ids:
            selected_sprint_id = sprint_ids[0]
            sprint_start_date = None
            sprint_end_date = None
            logger.info(f"No active sprint found, selected first: {selected_sprint_id}")
        else:
            logger.warning("No sprint snapshots available")
            from ui.sprint_tracker import create_no_sprints_state

            return create_no_sprints_state()

        sprint_data = sprint_snapshots[selected_sprint_id]

        logger.info(f"Selected sprint: {selected_sprint_id}")

        # Calculate sprint progress
        from data.sprint_manager import calculate_sprint_progress
        from data.persistence import load_app_settings

        settings = load_app_settings()
        flow_mappings = settings.get("field_mappings", {}).get("flow", {})
        flow_end_statuses = flow_mappings.get("flow_end_statuses", ["Done", "Closed"])
        flow_wip_statuses = flow_mappings.get("flow_wip_statuses", ["In Progress"])

        progress_data = calculate_sprint_progress(
            sprint_data, flow_end_statuses, flow_wip_statuses
        )

        # Detect sprint changes
        sprint_changes = detect_sprint_changes(changelog_entries)
        selected_sprint_changes = sprint_changes.get(selected_sprint_id, {})

        # Create UI components
        from ui.sprint_tracker import (
            create_sprint_summary_cards,
            create_sprint_selector,
            create_sprint_change_indicators,
            create_sprint_filters,
        )
        from visualization.sprint_charts import (
            create_sprint_progress_bars,
            create_sprint_summary_card,
        )

        # Build summary card data
        summary_card_data = create_sprint_summary_card(
            progress_data, show_points, flow_wip_statuses
        )

        # Create sprint summary cards
        summary_cards = create_sprint_summary_cards(
            selected_sprint_id, summary_card_data, show_points
        )

        # Create change indicators
        change_indicators = create_sprint_change_indicators(
            len(selected_sprint_changes.get("added", [])),
            len(selected_sprint_changes.get("removed", [])),
            len(selected_sprint_changes.get("moved_in", [])),
            len(selected_sprint_changes.get("moved_out", [])),
        )

        # Load status changelog for time-in-status calculation
        status_changelog = backend.get_changelog_entries(
            active_profile_id, active_query_id, field_name="status"
        )

        logger.info(
            f"[SPRINT TRACKER] Loaded {len(status_changelog)} status changelog entries for sprint"
        )

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
            sprint_changes=selected_sprint_changes,  # Pass sprint changes for icons
        )

        # Create sprint selector if multiple sprints
        sprint_selector = (
            create_sprint_selector(sprint_ids, selected_sprint_id)
            if len(sprint_ids) > 1
            else html.Div()
        )

        # Create filter controls
        filter_controls = create_sprint_filters()

        # Create compact legend for sprint changes (replaces large explanation alert)
        from ui.sprint_tracker import create_sprint_changes_legend

        changes_legend = create_sprint_changes_legend(
            len(selected_sprint_changes.get("added", [])),
            len(selected_sprint_changes.get("removed", [])),
            len(selected_sprint_changes.get("moved_in", [])),
            len(selected_sprint_changes.get("moved_out", [])),
        )

        # Assemble the complete layout
        return html.Div(
            [
                dbc.Container(
                    [
                        # Sprint selector
                        sprint_selector,
                        # Summary cards
                        summary_cards,
                        # Change indicators with compact legend
                        change_indicators,
                        changes_legend,
                        # Filter controls
                        filter_controls,
                        # Progress bars (HTML component)
                        html.H5("Issue Progress", className="mt-4 mb-3"),
                        progress_bars,
                    ],
                    fluid=True,
                    className="mt-4",
                )
            ]
        )

    except Exception as e:
        import traceback

        logger.error(f"Error rendering Sprint Tracker content: {e}")
        logger.error(traceback.format_exc())

        # Return error state
        return html.Div(
            [
                dbc.Alert(
                    [
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        html.Strong("Error: "),
                        f"Failed to load Sprint Tracker data: {str(e)}",
                    ],
                    color="danger",
                    className="m-4",
                )
            ]
        )
