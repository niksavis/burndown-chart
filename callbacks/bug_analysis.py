"""
Bug Analysis Callbacks Module

This module provides callback functions for the bug analysis feature,
handling bug metrics updates and interactivity with timeline filters.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
import logging

# Third-party library imports
from dash import Input, Output, callback
from dash import html

# Application imports
from data.bug_processing import filter_bug_issues, calculate_bug_metrics_summary
from data.persistence import load_unified_project_data
from ui.bug_analysis import create_bug_metrics_card
from configuration.settings import get_bug_analysis_config

#######################################################################
# LOGGING CONFIGURATION
#######################################################################
logger = logging.getLogger(__name__)

#######################################################################
# CALLBACK FUNCTIONS
#######################################################################


@callback(
    Output("bug-metrics-card", "children"),
    Input("chart-tabs", "active_tab"),
    prevent_initial_call=False,
)
def update_bug_metrics(active_tab: str):
    """
    Update bug metrics card when tab is activated.

    This callback listens to:
    - Tab activation (tab-bug-analysis)

    Args:
        active_tab: Currently active tab ID

    Returns:
        Dash component with bug metrics card content
    """
    # Only update when bug analysis tab is active
    if active_tab != "tab-bug-analysis":
        return html.Div()  # Return empty div for other tabs

    logger.info(f"Bug metrics callback triggered for tab: {active_tab}")

    try:
        # Load bug analysis configuration
        bug_config = get_bug_analysis_config()

        # Get JIRA issues - try multiple sources
        all_issues = []

        # First: Try project_data.json
        if not all_issues:
            project_data = load_unified_project_data()
            all_issues = project_data.get("jira_issues", [])
            logger.debug(f"Loaded {len(all_issues)} issues from project file")

        # Third: Try jira_cache.json directly
        if not all_issues:
            try:
                from data.jira_simple import load_jira_cache
                from data.persistence import load_app_settings, load_jira_configuration

                settings = load_app_settings()
                jira_config = load_jira_configuration()
                jql_query = settings.get("jql_query", "")

                # Include points field if configured (must match cached fields)
                base_fields = "key,created,resolutiondate,status,issuetype"
                points_field = jira_config.get("points_field", "")
                fields = (
                    f"{base_fields},{points_field}" if points_field else base_fields
                )

                cache_loaded, cached_issues = load_jira_cache(jql_query, fields)
                if cache_loaded and cached_issues:
                    all_issues = cached_issues
                    logger.debug(f"Loaded {len(all_issues)} issues from JIRA cache")
            except Exception as e:
                logger.warning(f"Could not load from JIRA cache: {e}")

        # Filter to bug issues only
        bug_issues = filter_bug_issues(
            all_issues,
            bug_type_mappings=bug_config.get("issue_type_mappings", {}),
        )

        logger.info(
            f"Filtered to {len(bug_issues)} bug issues from {len(all_issues)} total"
        )

        # Note: Timeline filtering will be added in Phase 4 - Bug Trends
        # For now, use all filtered bug issues without date range filtering

        # Calculate bug metrics (weekly_stats=[] for now - will enhance later)
        bug_metrics = calculate_bug_metrics_summary(bug_issues, weekly_stats=[])

        logger.debug(
            f"Calculated metrics: {bug_metrics['total_bugs']} total, "
            f"{bug_metrics['open_bugs']} open, "
            f"{bug_metrics['resolution_rate']:.1%} resolution rate"
        )

        # Create and return metrics card
        return create_bug_metrics_card(bug_metrics)

    except Exception as e:
        logger.error(f"Error updating bug metrics: {e}", exc_info=True)
        return html.Div(
            [
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Error loading bug metrics: {str(e)}",
            ],
            className="alert alert-danger",
        )


#######################################################################
# CALLBACK REGISTRATION
#######################################################################


def register(app):
    """
    Register bug analysis callbacks with the app.

    Note: The @callback decorator auto-registers, but this function
    ensures the module is loaded and provides a consistent registration pattern.
    """
    # Callbacks are auto-registered via @callback decorator when module is imported
    logger.info("Bug analysis callbacks registered")
    pass
