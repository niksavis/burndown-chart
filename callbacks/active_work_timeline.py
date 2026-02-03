"""Active Work Timeline Callbacks Module

This module provides callback functions for the Active Work Timeline feature,
handling epic/feature timeline rendering with recent activity.

Follows Sprint Tracker pattern for conditional tab display.
"""

import logging
from dash import html
import dash_bootstrap_components as dbc

logger = logging.getLogger(__name__)


def _render_active_work_timeline_content(show_points: bool = False) -> html.Div:
    """Render Active Work Timeline content with epic timeline and issue lists.

    Structure:
    1. Timeline visualization (top) - Epic aggregation
    2. Last Week issues list with health indicators
    3. This Week issues list with health indicators

    Args:
        show_points: Whether to show story points metrics

    Returns:
        Div containing timeline layout with issue lists
    """
    try:
        from data.persistence.factory import get_backend
        from data.active_work_manager import get_active_work_data
        from ui.active_work_timeline import (
            create_no_issues_state,
            create_timeline_visualization,
            create_issue_list_section,
        )

        backend = get_backend()

        # Get active profile and query
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            logger.warning("No active profile/query - cannot render timeline")
            return create_no_issues_state()

        logger.info(
            f"Rendering Active Work Timeline for profile={active_profile_id}, query={active_query_id}"
        )

        # Load issues from database
        issues = backend.get_issues(
            profile_id=active_profile_id, query_id=active_query_id
        )

        if not issues:
            logger.info("No issues found for active profile/query")
            return create_no_issues_state()

        logger.info(f"Loaded {len(issues)} issues from database")

        # Get configuration
        from data.persistence import load_app_settings

        settings = load_app_settings()
        field_mappings = settings.get("field_mappings", {})
        general_mappings = field_mappings.get("general", {})
        workflow_mappings = field_mappings.get("workflow", {})

        parent_field = general_mappings.get("parent_field")
        flow_end_statuses = workflow_mappings.get("flow_end_statuses", [])
        flow_wip_statuses = workflow_mappings.get("flow_wip_statuses", [])

        # Check if parent field is configured
        parent_field_configured = bool(parent_field)

        if not parent_field_configured:
            logger.info(
                "Parent field not configured - will show issues without epic timeline"
            )
            # Use dummy parent field to still process issues
            parent_field = "parent"  # Won't match anything, all issues will be orphaned

        logger.info(
            f"Using parent field: {parent_field} (configured: {parent_field_configured})"
        )

        # Get active work data (timeline + issue lists)
        work_data = get_active_work_data(
            issues,
            parent_field=parent_field,
            flow_end_statuses=flow_end_statuses if flow_end_statuses else None,
            flow_wip_statuses=flow_wip_statuses if flow_wip_statuses else None,
        )

        timeline = work_data["timeline"]
        last_week_issues = work_data["last_week_issues"]
        this_week_issues = work_data["this_week_issues"]

        if not timeline and not last_week_issues and not this_week_issues:
            logger.info("No active work found")
            return create_no_issues_state(
                parent_field_configured=parent_field_configured
            )

        logger.info(
            f"Found {len(timeline)} epics, {len(last_week_issues)} last week issues, "
            f"{len(this_week_issues)} this week issues"
        )

        # Create components
        if parent_field_configured and timeline:
            # Show epic timeline
            timeline_section = create_timeline_visualization(timeline, show_points)
        else:
            # Show info message about parent field configuration
            timeline_section = dbc.Alert(
                [
                    html.I(className="fas fa-info-circle me-2"),
                    "To see epic timeline, configure the ",
                    html.Strong("Parent/Epic Field"),
                    " in Settings → Fields tab → General Fields. ",
                    "Issues are shown below without epic grouping.",
                ],
                color="info",
                className="mb-4",
            )
        last_week_section = create_issue_list_section(
            "Last Week", last_week_issues, show_points
        )
        this_week_section = create_issue_list_section(
            "This Week", this_week_issues, show_points
        )

        # Assemble layout
        return html.Div(
            [
                dbc.Container(
                    [
                        # Header
                        html.Div(
                            [
                                html.H3(
                                    [
                                        html.I(
                                            className="fas fa-project-diagram me-2 text-primary"
                                        ),
                                        "Active Work Timeline",
                                    ],
                                    className="mb-2",
                                ),
                                html.P(
                                    f"Showing {len(timeline)} epics with {len(last_week_issues) + len(this_week_issues)} active issues (last 2 weeks)",
                                    className="text-muted mb-4",
                                ),
                            ]
                        ),
                        # Timeline at top
                        timeline_section,
                        html.Hr(className="my-4"),
                        # Issue lists below
                        last_week_section,
                        html.Hr(className="my-4"),
                        this_week_section,
                    ],
                    fluid=True,
                    className="py-3",
                )
            ]
        )

    except Exception as e:
        logger.error(f"Error rendering Active Work Timeline: {e}", exc_info=True)
        from ui.active_work_timeline import create_no_issues_state

        return create_no_issues_state()


def register(app):
    """Register Active Work Timeline callbacks.

    Args:
        app: Dash application instance
    """
    # Currently no interactive callbacks needed for Phase 3
    # Phase 4 will add filtering callbacks for days_back slider
    pass
