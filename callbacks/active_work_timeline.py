"""Active Work Timeline Callbacks Module

This module provides callback functions for the Active Work Timeline feature,
handling epic/feature timeline rendering with recent activity.

Follows Sprint Tracker pattern for conditional tab display.
"""

import logging
from dash import html
import dash_bootstrap_components as dbc

logger = logging.getLogger(__name__)


def _render_active_work_timeline_content(show_points: bool = False, data_points_count: int = 30) -> html.Div:
    """Render Active Work Timeline content with nested epic timeline.

    Structure:
    1. Epic Timeline with nested issues (sorted: Blocked/WIP → To Do → Completed)
    2. Issues filtered by data_points_count date range

    Args:
        show_points: Whether to show story points metrics
        data_points_count: Number of days to look back (from Data Points slider)

    Returns:
        Div containing nested epic timeline
    """
    try:
        from data.persistence.factory import get_backend
        from data.active_work_manager import get_active_work_data
        from ui.active_work_timeline import (
            create_no_issues_state,
            create_nested_epic_timeline,
        )

        backend = get_backend()

        # Get active profile and query
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            logger.warning("No active profile/query - cannot render timeline")
            return create_no_issues_state()

        logger.info(
            f"[ACTIVE WORK] Rendering Active Work Timeline for profile={active_profile_id}, query={active_query_id}, data_points={data_points_count}"
        )

        # Load issues from database
        issues = backend.get_issues(
            profile_id=active_profile_id, query_id=active_query_id
        )

        if not issues:
            logger.warning("[ACTIVE WORK] No issues found for active profile/query")
            return create_no_issues_state()

        logger.info(f"[ACTIVE WORK] Loaded {len(issues)} issues from database")

        # Get configuration
        from data.persistence import load_app_settings

        settings = load_app_settings()
        field_mappings = settings.get("field_mappings", {})
        general_mappings = field_mappings.get("general", {})
        workflow_mappings = field_mappings.get("workflow", {})

        parent_field = general_mappings.get("parent_field")
        flow_end_statuses = workflow_mappings.get("flow_end_statuses", [])
        flow_wip_statuses = workflow_mappings.get("flow_wip_statuses", [])
        development_projects = settings.get("development_projects", [])
        devops_projects = settings.get("devops_projects", [])
        
        # DEBUG: Log configuration
        logger.info(f"[ACTIVE WORK DEBUG] development_projects: {development_projects}")
        logger.info(f"[ACTIVE WORK DEBUG] devops_projects: {devops_projects}")
        logger.info(f"[ACTIVE WORK DEBUG] Before filtering: {len(issues)} total issues")
        
        # Filter to only configured development project issues
        from data.project_filter import filter_development_issues
        
        issues = filter_development_issues(issues, development_projects, devops_projects)
        logger.info(f"[ACTIVE WORK] After project filtering: {len(issues)} development issues")

        # Check if parent field is configured
        parent_field_configured = bool(parent_field)

        if not parent_field_configured:
            logger.info(
                "Parent field not configured - will show issues without epic timeline"
            )
            # Use dummy parent field to still process issues
            parent_field = "parent"  # Won't match anything, all issues will be orphaned

        logger.info(
            f"[ACTIVE WORK] Using parent field: {parent_field} (configured: {parent_field_configured})"
        )

        # Get active work data with nested structure
        try:
            logger.info(f"[ACTIVE WORK] Calling get_active_work_data with {len(issues)} issues...")
            work_data = get_active_work_data(
                issues,
                backend=backend,
                profile_id=active_profile_id,
                query_id=active_query_id,
                data_points_count=data_points_count,
                parent_field=parent_field,
                flow_end_statuses=flow_end_statuses if flow_end_statuses else None,
                flow_wip_statuses=flow_wip_statuses if flow_wip_statuses else None,
                filter_parents=True,  # Filter out parent issues from child calculations
            )
            logger.info(f"[ACTIVE WORK] get_active_work_data returned successfully")
        except Exception as e:
            logger.error(f"[ACTIVE WORK] Error in get_active_work_data: {e}", exc_info=True)
            return create_no_issues_state(
                parent_field_configured=parent_field_configured
            )
        
        timeline = work_data.get("timeline", [])
        
        logger.info(
            f"[ACTIVE WORK] Got work_data: timeline={len(timeline)} epics"
        )

        if not timeline:
            logger.warning("[ACTIVE WORK] No active work found after filtering - empty timeline")
            return create_no_issues_state(
                parent_field_configured=parent_field_configured
            )

        # Count total issues across all epics
        total_issues = sum(epic.get("total_issues", 0) for epic in timeline)

        logger.info(
            f"Found {len(timeline)} epics with {total_issues} total issues"
        )

        # Create nested epic timeline
        timeline_content = create_nested_epic_timeline(
            timeline, show_points, parent_field_configured
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
                                    f"Showing {len(timeline)} epics with {total_issues} issues (within last {data_points_count} days)",
                                    className="text-muted mb-4",
                                ),
                            ]
                        ),
                        # Nested epic timeline
                        timeline_content,
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
    # No callbacks needed - all epics displayed expanded
    # Collapse functionality removed to avoid Dash callback conflicts
    pass

