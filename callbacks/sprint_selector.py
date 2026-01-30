"""Sprint Tracker Dropdown Callback

Handles sprint selection changes in the Sprint Tracker tab.
"""

import logging
from dash import callback, Input, Output, State, html, dcc, no_update
import dash_bootstrap_components as dbc

logger = logging.getLogger(__name__)


@callback(
    Output("sprint-tracker-tab-content", "children", allow_duplicate=True),
    Input("sprint-selector-dropdown", "value"),
    State("timeline-slider", "value"),
    State("points-toggle", "value"),
    prevent_initial_call=True,
)
def update_sprint_selection(
    selected_sprint: str, data_points_count: int, show_points_list: list
):
    """Update Sprint Tracker tab when user selects a different sprint.

    Args:
        selected_sprint: Sprint name/ID selected from dropdown
        data_points_count: Number of weeks from timeline slider (not used here)
        show_points_list: Story points toggle state

    Returns:
        Updated Sprint Tracker content for the selected sprint
    """
    if not selected_sprint:
        return no_update

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
        sprint_snapshots = get_sprint_snapshots(tracked_issues, changelog_entries)

        if selected_sprint not in sprint_snapshots:
            logger.warning(f"Selected sprint {selected_sprint} not found in snapshots")
            return no_update

        # Get selected sprint data
        sprint_data = sprint_snapshots[selected_sprint]

        # Calculate progress
        from data.sprint_manager import calculate_sprint_progress, detect_sprint_changes

        flow_mappings = settings.get("field_mappings", {}).get("flow", {})
        flow_end_statuses = flow_mappings.get("flow_end_statuses", ["Done", "Closed"])
        flow_wip_statuses = flow_mappings.get("flow_wip_statuses", ["In Progress"])

        progress_data = calculate_sprint_progress(sprint_data, flow_end_statuses)
        sprint_changes = detect_sprint_changes(changelog_entries)
        selected_sprint_changes = sprint_changes.get(selected_sprint, {})

        # Create UI components
        from ui.sprint_tracker import (
            create_sprint_summary_cards,
            create_sprint_selector,
            create_sprint_change_indicators,
            create_sprint_filters,
        )
        from visualization.sprint_charts import (
            create_sprint_progress_bars,
            create_sprint_timeline_chart,
            create_status_distribution_pie,
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

        # Create visualizations
        progress_bars = create_sprint_progress_bars(
            sprint_data, status_changelog, show_points
        )
        timeline_chart = create_sprint_timeline_chart(selected_sprint_changes)
        status_pie = create_status_distribution_pie(progress_data)

        # Create sprint selector (keep all sprints available)
        sprint_ids = sorted(sprint_snapshots.keys(), reverse=True)
        sprint_selector = (
            create_sprint_selector(sprint_ids, selected_sprint)
            if len(sprint_ids) > 1
            else html.Div()
        )

        # Create filter controls
        filter_controls = create_sprint_filters()

        # Add explanation tooltips
        explanation_note = dbc.Alert(
            [
                html.Strong("Sprint Changes Explained:", className="me-2"),
                html.Br(),
                html.Small(
                    [
                        html.Strong("Added: "),
                        "Issues that were added to this sprint.",
                        html.Br(),
                        html.Strong("Moved In: "),
                        "Issues transferred from another sprint to this sprint.",
                        html.Br(),
                        html.Strong("Moved Out: "),
                        "Issues moved from this sprint to a different sprint (e.g., moved to a future sprint).",
                        html.Br(),
                        html.Strong("Removed: "),
                        "Issues moved back to backlog (no sprint assigned).",
                        html.Br(),
                        html.Em(
                            "Note: Only Story, Task, and Bug issue types are tracked (sub-tasks excluded)."
                        ),
                    ]
                ),
            ],
            color="info",
            className="mb-3 mt-3",
        )

        # Assemble layout
        return html.Div(
            [
                dbc.Container(
                    [
                        sprint_selector,
                        summary_cards,
                        change_indicators,
                        explanation_note,
                        filter_controls,
                        # Progress bars
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.H5("Issue Progress", className="mb-3"),
                                        dcc.Graph(
                                            figure=progress_bars,
                                            config={
                                                "displayModeBar": False,
                                                "responsive": True,
                                            },
                                            style={"height": "450px"},
                                        ),
                                    ],
                                    xs=12,
                                    className="mb-4",
                                )
                            ]
                        ),
                        # Timeline and distribution
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.H5(
                                            "Sprint Composition Changes",
                                            className="mb-3",
                                        ),
                                        dcc.Graph(
                                            figure=timeline_chart,
                                            config={"displayModeBar": False},
                                            style={"height": "400px"},
                                        ),
                                    ],
                                    xs=12,
                                    md=6,
                                    className="mb-4",
                                ),
                                dbc.Col(
                                    [
                                        html.H5(
                                            "Status Distribution", className="mb-3"
                                        ),
                                        dcc.Graph(
                                            figure=status_pie,
                                            config={"displayModeBar": False},
                                            style={"height": "450px"},
                                        ),
                                    ],
                                    xs=12,
                                    md=6,
                                    className="mb-4",
                                ),
                            ]
                        ),
                    ],
                    fluid=True,
                    className="mt-4",
                )
            ]
        )

    except Exception as e:
        import traceback

        logger.error(f"Error updating sprint selection: {e}")
        logger.error(traceback.format_exc())

        return dbc.Alert(
            [
                html.I(className="fas fa-exclamation-triangle me-2"),
                html.Strong("Error: "),
                f"Failed to load sprint data: {str(e)}",
            ],
            color="danger",
            className="m-4",
        )
