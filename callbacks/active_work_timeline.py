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
    """Render Active Work Timeline content with active epics.

    Args:
        show_points: Whether to show story points metrics

    Returns:
        Div containing timeline layout with epic cards
    """
    try:
        from data.persistence.factory import get_backend
        from data.active_work_manager import get_active_epics
        from ui.active_work_timeline import (
            create_no_epics_state,
            create_epic_card,
        )

        backend = get_backend()

        # Get active profile and query
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            logger.warning("No active profile/query - cannot render timeline")
            return create_no_epics_state()

        logger.info(
            f"Rendering Active Work Timeline for profile={active_profile_id}, query={active_query_id}"
        )

        # Load issues from database
        issues = backend.get_issues(
            profile_id=active_profile_id, query_id=active_query_id
        )

        if not issues:
            logger.info("No issues found for active profile/query")
            return create_no_epics_state()

        logger.info(f"Loaded {len(issues)} issues from database")

        # Get parent field from configuration
        # Load field mappings from profile settings
        from data.persistence import load_app_settings

        settings = load_app_settings()
        field_mappings = settings.get("field_mappings", {})
        general_mappings = field_mappings.get("general", {})
        parent_field = general_mappings.get("parent_field")

        if not parent_field:
            logger.warning("Parent field not configured in field mappings")
            return create_no_epics_state()

        logger.info(f"Using parent field: {parent_field}")

        # Get active epics with recent activity (last 7 days + current week)
        active_epics = get_active_epics(
            issues, days_back=7, include_current_week=True, parent_field=parent_field
        )

        if not active_epics:
            logger.info("No active epics found with recent activity")
            return create_no_epics_state()

        logger.info(f"Found {len(active_epics)} active epics with recent activity")

        # Create epic cards
        epic_cards = [create_epic_card(epic, show_points) for epic in active_epics]

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
                                        "Active Work",
                                    ],
                                    className="mb-2",
                                ),
                                html.P(
                                    f"Showing {len(active_epics)} epics/features with activity in last 7 days or current week",
                                    className="text-muted mb-4",
                                ),
                            ]
                        ),
                        # Controls (future: filtering)
                        # controls,  # Disabled for Phase 3 - can enable in Phase 4
                        # Epic cards
                        html.Div(epic_cards, id="active-epics-container"),
                    ],
                    fluid=True,
                    className="py-3",
                )
            ]
        )

    except Exception as e:
        logger.error(f"Error rendering Active Work Timeline: {e}", exc_info=True)
        from ui.active_work_timeline import create_no_epics_state

        return create_no_epics_state()


def register(app):
    """Register Active Work Timeline callbacks.

    Args:
        app: Dash application instance
    """
    # Currently no interactive callbacks needed for Phase 3
    # Phase 4 will add filtering callbacks for days_back slider
    pass
