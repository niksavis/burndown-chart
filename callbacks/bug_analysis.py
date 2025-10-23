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
from dash import Input, Output, callback, no_update
from dash import html
import dash_bootstrap_components as dbc

# Application imports
from data.bug_processing import (
    filter_bug_issues,
    calculate_bug_metrics_summary,
    forecast_bug_resolution,
)
from data.persistence import load_unified_project_data
from ui.bug_analysis import (
    create_bug_metrics_card,
    create_quality_insights_panel,
    create_bug_forecast_card,
)
from data.bug_insights import generate_quality_insights
from configuration.settings import get_bug_analysis_config

#######################################################################
# LOGGING CONFIGURATION
#######################################################################
logger = logging.getLogger(__name__)

#######################################################################
# CALLBACK FUNCTIONS
#######################################################################


@callback(
    Output("bug-analysis-tab-content", "children"),
    [Input("chart-tabs", "active_tab"), Input("data-points-input", "value")],
    prevent_initial_call=False,
)
def update_bug_metrics(active_tab: str, data_points_count: int):
    """
    Update bug analysis tab content when tab is activated or timeline changes.

    This callback follows the same pattern as other tabs (Items per Week, etc.)
    by returning the entire tab content instead of updating nested placeholder divs.
    This prevents issues with click events and chart disappearance.

    This callback listens to:
    - Tab activation (tab-bug-analysis)
    - Timeline filter changes (data-points-input) - T042

    Args:
        active_tab: Currently active tab ID
        data_points_count: Number of weeks to include (from timeline filter)

    Returns:
        Complete bug analysis tab content (html.Div)
    """
    # Only update when bug analysis tab is active
    if active_tab != "tab-bug-analysis":
        logger.debug(f"Skipping update for inactive tab: {active_tab}")
        return no_update  # Don't update if not our tab

    logger.info(
        f"Bug metrics callback triggered for tab: {active_tab}, data_points: {data_points_count}"
    )

    try:
        # Load bug analysis configuration
        bug_config = get_bug_analysis_config()

        # Get JIRA configuration for points field
        from data.persistence import load_jira_configuration

        jira_config = load_jira_configuration()
        points_field = jira_config.get("points_field", "customfield_10016")

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
                from data.persistence import load_app_settings

                settings = load_app_settings()
                jql_query = settings.get("jql_query", "")

                # Include points field if configured (must match cached fields)
                base_fields = "key,created,resolutiondate,status,issuetype"
                fields = (
                    f"{base_fields},{points_field}" if points_field else base_fields
                )

                cache_loaded, cached_issues = load_jira_cache(jql_query, fields)
                if cache_loaded and cached_issues:
                    all_issues = cached_issues
                    logger.debug(f"Loaded {len(all_issues)} issues from JIRA cache")
            except Exception as e:
                logger.warning(f"Could not load from JIRA cache: {e}")

        # Determine date range based on data_points_count (timeline filter)
        from datetime import datetime, timedelta

        date_to = datetime.now()
        date_from = date_to - timedelta(weeks=data_points_count or 12)

        # Get ALL bugs (without date filter) for current state metrics (open bugs count)
        all_bug_issues = filter_bug_issues(
            all_issues,
            bug_type_mappings=bug_config.get("issue_type_mappings", {}),
            date_from=None,  # No date filter for current state
            date_to=None,
        )

        # Get timeline-filtered bugs for historical trend analysis
        timeline_filtered_bugs = filter_bug_issues(
            all_issues,
            bug_type_mappings=bug_config.get("issue_type_mappings", {}),
            date_from=date_from,
            date_to=date_to,
        )

        logger.info(
            f"Total bug issues: {len(all_bug_issues)} (all time), "
            f"{len(timeline_filtered_bugs)} in selected timeline "
            f"(date range: {date_from.date()} to {date_to.date()}, {data_points_count} weeks)"
        )

        # Initialize weekly_stats (needed for quality insights)
        weekly_stats = []

        # Calculate weekly bug statistics using timeline-filtered bugs
        try:
            logger.info(
                f"Attempting to calculate statistics with {len(timeline_filtered_bugs)} bugs from {date_from} to {date_to}"
            )
            from data.bug_processing import calculate_bug_statistics

            weekly_stats = calculate_bug_statistics(
                timeline_filtered_bugs, date_from, date_to, story_points_field=points_field
            )

            logger.info(
                f"Successfully calculated {len(weekly_stats)} weeks of statistics"
            )

            # Calculate bug metrics summary
            # Use all_bug_issues for current state (open bugs count)
            # Use timeline_filtered_bugs for historical metrics (resolution rate, trends)
            bug_metrics = calculate_bug_metrics_summary(
                all_bug_issues, timeline_filtered_bugs, weekly_stats
            )

            logger.debug(
                f"Calculated metrics: {bug_metrics['total_bugs']} total, "
                f"{bug_metrics['open_bugs']} open, "
                f"{bug_metrics['resolution_rate']:.1%} resolution rate"
            )

            # Create metrics card
            metrics_card = create_bug_metrics_card(bug_metrics)

            # Create bug trends chart
            from ui.bug_charts import BugTrendChart, BugInvestmentChart

            trends_chart = BugTrendChart(weekly_stats, viewport_size="mobile")

            # T056: Create bug investment chart (items + story points)
            # T057: Check if story points data is available
            has_story_points = any(
                stat.get("bugs_points_created", 0) > 0
                or stat.get("bugs_points_resolved", 0) > 0
                for stat in weekly_stats
            )

            if has_story_points:
                investment_chart = BugInvestmentChart(
                    weekly_stats, viewport_size="mobile"
                )
            else:
                # T057: Show message when no story points
                investment_chart = dbc.Card(
                    dbc.CardBody(
                        [
                            html.H5(
                                "Bug Investment Chart",
                                className="card-title",
                            ),
                            html.Div(
                                [
                                    html.I(className="fas fa-info-circle me-2"),
                                    html.Span(
                                        "Story points data not available for this project. "
                                        "Only bug item counts are being tracked."
                                    ),
                                ],
                                className="alert alert-info",
                            ),
                        ]
                    ),
                    className="mb-3",
                )
        except ValueError as ve:
            # Handle edge case: not enough bugs for statistics
            logger.error(f"Could not calculate bug statistics: {ve}")
            logger.error(
                f"Bug count: {len(timeline_filtered_bugs)}, date_from: {date_from}, date_to: {date_to}"
            )
            # Set empty weekly_stats for insights
            weekly_stats = []

            # Calculate bug metrics even if statistics failed (for basic metrics card)
            bug_metrics = calculate_bug_metrics_summary(
                all_bug_issues, timeline_filtered_bugs, weekly_stats=[]
            )
            metrics_card = create_bug_metrics_card(bug_metrics)

            trends_chart = dbc.Card(
                dbc.CardBody(
                    [
                        html.I(className="fas fa-info-circle me-2"),
                        f"Not enough bug data to display trends. ({ve})",
                    ]
                ),
                className="border-info bg-light text-info mb-3",
            )
            investment_chart = dbc.Card(
                dbc.CardBody(
                    [
                        html.I(className="fas fa-info-circle me-2"),
                        "Not enough bug data to display investment metrics.",
                    ]
                ),
                className="border-info bg-light text-info mb-3",
            )

        # Return complete tab content (matches Items per Week pattern)
        return html.Div(
            [
                # Header
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H2(
                                    [
                                        html.I(className="fas fa-bug me-2"),
                                        "Bug Analysis Dashboard",
                                    ],
                                    className="mb-3",
                                ),
                                html.P(
                                    "Track bug creation, resolution trends, and quality metrics to maintain project health.",
                                    className="text-muted",
                                ),
                            ]
                        )
                    ],
                    className="mb-4",
                ),
                # Bug metrics card
                dbc.Row([dbc.Col([metrics_card], width=12)], className="mb-4"),
                # Bug forecast card (T098-T104)
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                create_bug_forecast_card(
                                    forecast_bug_resolution(
                                        bug_metrics.get("open_bugs", 0),
                                        weekly_stats,
                                        use_last_n_weeks=8,
                                    ),
                                    bug_metrics.get("open_bugs", 0),
                                )
                            ],
                            width=12,
                        )
                    ],
                    className="mb-4",
                ),
                # Bug trends chart
                dbc.Row([dbc.Col([trends_chart], width=12)], className="mb-4"),
                # T056: Bug investment chart (items + story points)
                dbc.Row([dbc.Col([investment_chart], width=12)], className="mb-4"),
                # Quality insights panel (T078-T082)
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                # Generate quality insights from metrics and statistics
                                create_quality_insights_panel(
                                    generate_quality_insights(bug_metrics, weekly_stats)
                                )
                            ],
                            width=12,
                        )
                    ]
                ),
            ]
        )

    except Exception as e:
        logger.error(f"Error updating bug metrics: {e}", exc_info=True)
        # Return complete error page (not just error cards)
        return html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H2(
                                    [
                                        html.I(className="fas fa-bug me-2"),
                                        "Bug Analysis Dashboard",
                                    ],
                                    className="mb-3",
                                ),
                            ]
                        )
                    ],
                    className="mb-4",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.I(
                                                className="fas fa-exclamation-triangle me-2"
                                            ),
                                            f"Error loading bug analysis: {str(e)}",
                                        ]
                                    ),
                                    className="border-danger bg-light text-danger mb-3",
                                )
                            ],
                            width=12,
                        )
                    ]
                ),
            ]
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
