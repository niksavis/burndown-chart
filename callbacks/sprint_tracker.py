"""Sprint Tracker Callbacks Module

This module provides callback functions for the Sprint Tracker feature,
handling sprint data rendering and filtering.

Follows Bug Analysis pattern for conditional tab display.
"""

import logging
from dash import html, dcc
import dash_bootstrap_components as dbc

logger = logging.getLogger(__name__)


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

        # Load sprint changelog entries
        changelog_entries = backend.get_changelog_entries(
            active_profile_id, active_query_id, field_name="sprint"
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

        # Select first sprint (or could add sprint selector logic)
        sprint_ids = sorted(sprint_snapshots.keys(), reverse=True)  # Newest first
        selected_sprint_id = sprint_ids[0]
        sprint_data = sprint_snapshots[selected_sprint_id]

        logger.info(f"Selected sprint: {selected_sprint_id}")

        # Calculate sprint progress
        from data.sprint_manager import calculate_sprint_progress
        from data.persistence import load_app_settings

        settings = load_app_settings()
        flow_mappings = settings.get("field_mappings", {}).get("flow", {})
        flow_end_statuses = flow_mappings.get("flow_end_statuses", ["Done", "Closed"])

        progress_data = calculate_sprint_progress(sprint_data, flow_end_statuses)

        # Detect sprint changes
        sprint_changes = detect_sprint_changes(changelog_entries)
        selected_sprint_changes = sprint_changes.get(selected_sprint_id, {})

        # Create UI components
        from ui.sprint_tracker import (
            create_sprint_summary_cards,
            create_sprint_selector,
            create_sprint_change_indicators,
        )
        from visualization.sprint_charts import (
            create_sprint_progress_bars,
            create_sprint_timeline_chart,
            create_status_distribution_pie,
            create_sprint_summary_card,
        )

        # Build summary card data
        summary_card_data = create_sprint_summary_card(progress_data, show_points)

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

        # Create visualizations
        progress_bars = create_sprint_progress_bars(
            sprint_data, status_changelog, show_points
        )

        timeline_chart = create_sprint_timeline_chart(selected_sprint_changes)

        status_pie = create_status_distribution_pie(progress_data)

        # Create sprint selector if multiple sprints
        sprint_selector = (
            create_sprint_selector(sprint_ids) if len(sprint_ids) > 1 else html.Div()
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
                        # Change indicators
                        change_indicators,
                        # Progress bars
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.H5("Issue Progress", className="mb-3"),
                                        dcc.Graph(
                                            figure=progress_bars,
                                            config={"displayModeBar": False},
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
