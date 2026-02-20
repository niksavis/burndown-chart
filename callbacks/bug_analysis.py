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

import dash_bootstrap_components as dbc

# Third-party library imports
from dash import html

from configuration.settings import get_bug_analysis_config
from data.bug_insights import generate_quality_insights

# Application imports
from data.bug_processing import (
    calculate_bug_metrics_summary,
    filter_bug_issues,
    forecast_bug_resolution,
)
from ui.bug_analysis import (
    create_bug_metrics_cards,
    create_quality_insights_panel,
)

#######################################################################
# LOGGING CONFIGURATION
#######################################################################
logger = logging.getLogger(__name__)

#######################################################################
# CALLBACK FUNCTIONS
#######################################################################


def _render_bug_analysis_content(
    data_points_count: int, show_points: bool = True, has_points_data: bool = False
):
    """
    Render bug analysis tab content.

    This is the core rendering logic extracted from the callback so it can be
    called directly from the main visualization callback for instant rendering
    without the "Loading bug analysis..." placeholder.

    Args:
        data_points_count: Number of weeks to include (from timeline filter)
        show_points: Whether points tracking is enabled
        has_points_data: Whether points data exists in the filtered time period

    Returns:
        Complete bug analysis tab content (html.Div)
    """
    logger.info(f"Rendering bug analysis content with data_points: {data_points_count}")

    try:
        # Load bug analysis configuration
        bug_config = get_bug_analysis_config()

        # Get JIRA configuration for points field
        from data.persistence import load_jira_configuration

        jira_config = load_jira_configuration()
        points_field = jira_config.get("points_field", "")

        # Get JIRA issues from cache with ALL fields (don't specify fields to avoid validation mismatch)
        # By passing empty string for fields, load_jira_cache won't validate fields
        all_issues = []

        try:
            # Load from database via backend
            from data.persistence.factory import get_backend

            backend = get_backend()
            active_profile_id = backend.get_app_state("active_profile_id")
            active_query_id = backend.get_app_state("active_query_id")

            # Get all issues from database
            if active_profile_id and active_query_id:
                all_issues = backend.get_issues(active_profile_id, active_query_id)

                if all_issues:
                    logger.debug(
                        f"Loaded {len(all_issues)} issues from database for {active_profile_id}/{active_query_id}"
                    )
                else:
                    logger.warning(
                        f"No issues found in database for {active_profile_id}/{active_query_id}"
                    )
            else:
                logger.warning(
                    f"No active profile/query configured: profile_id={active_profile_id}, query_id={active_query_id}"
                )
        except Exception as e:
            logger.warning(f"Could not load from JIRA cache: {e}")

        # Filter to only configured development project issues (exclude parents/parent types)
        if all_issues:
            from data.issue_filtering import filter_issues_for_metrics
            from data.persistence import load_app_settings

            settings = load_app_settings()

            original_count = len(all_issues)
            all_issues = filter_issues_for_metrics(
                all_issues, settings=settings, log_prefix="BUG ANALYSIS"
            )
            filtered_count = original_count - len(all_issues)
            if filtered_count > 0:
                logger.info(
                    f"Bug Analysis: Filtered to {len(all_issues)} development project issues from {original_count} total"
                )

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

        # Check if there are no bugs at all - show helpful placeholder
        if len(all_bug_issues) == 0:
            from ui.empty_states import create_no_bugs_state

            # Return empty state in fluid container to match DORA/Flow dashboards
            # Wrap in div with ID for fade-in animation
            return html.Div(
                dbc.Container(
                    create_no_bugs_state(),
                    fluid=True,
                    className="py-4",
                ),
                id="bug-analysis-tab-content",
            )

        # Initialize weekly_stats (needed for quality insights)
        weekly_stats = []

        # Check if there are no bugs in the timeline - show specific placeholder
        if len(timeline_filtered_bugs) == 0 and len(all_bug_issues) > 0:
            from ui.loading_utils import create_content_placeholder

            # Wrap in div with ID for fade-in animation
            return html.Div(
                create_content_placeholder(
                    type="chart",
                    text=f"No bug data in selected timeframe. Found {len(all_bug_issues)} total bugs, but none in the last {data_points_count} weeks. Use the Data Points slider in Settings to expand the timeline.",
                    icon="fa-calendar-times",
                    height="400px",
                ),
                id="bug-analysis-tab-content",
            )

        # Calculate weekly bug statistics using timeline-filtered bugs
        try:
            logger.info(
                f"Attempting to calculate statistics with {len(timeline_filtered_bugs)} bugs from {date_from} to {date_to}"
            )
            from data.bug_processing import calculate_bug_statistics

            weekly_stats = calculate_bug_statistics(
                timeline_filtered_bugs,
                date_from,
                date_to,
                story_points_field=points_field,
            )

            logger.info(
                f"Successfully calculated {len(weekly_stats)} weeks of statistics"
            )

            # Calculate bug metrics summary
            # Use all_bug_issues for current state (open bugs count)
            # Use timeline_filtered_bugs for historical metrics (resolution rate, trends)
            # Pass all_issues for total project capacity calculation
            bug_metrics = calculate_bug_metrics_summary(
                all_bug_issues,
                timeline_filtered_bugs,
                weekly_stats,
                date_from,
                date_to,
                all_project_issues=all_issues,
            )

            logger.debug(
                f"Calculated metrics: {bug_metrics['total_bugs']} total, "
                f"{bug_metrics['open_bugs']} open, "
                f"{bug_metrics['resolution_rate']:.1%} resolution rate"
            )

            # Calculate forecast for Expected Resolution card
            forecast = forecast_bug_resolution(
                bug_metrics.get("open_bugs", 0),
                weekly_stats,
                use_last_n_weeks=8,
            )

            # Create combined metrics cards (Resolution Rate + Open Bugs + Expected Resolution)
            metrics_cards = create_bug_metrics_cards(bug_metrics, forecast)

            # Create bug trends chart
            from ui.bug_charts import BugInvestmentChart, BugTrendChart

            trends_chart = BugTrendChart(weekly_stats, viewport_size="mobile")

            # T056: Create bug investment chart (items + story points)
            # T057: Check if story points data is available
            # Check both weekly aggregations AND raw bug data for story points
            has_story_points_in_stats = any(
                stat.get("bugs_points_created", 0) > 0
                or stat.get("bugs_points_resolved", 0) > 0
                for stat in weekly_stats
            )

            # Also check if ANY bugs have story points assigned
            # This catches cases where weekly_stats might be empty but bugs have points
            has_story_points_in_bugs = any(
                (bug.get("points") or bug.get("fields", {}).get(points_field, 0) or 0)
                > 0
                for bug in (
                    timeline_filtered_bugs if timeline_filtered_bugs else all_bug_issues
                )
            )

            has_story_points = has_story_points_in_stats or has_story_points_in_bugs

            logger.info(
                f"[BUG ANALYSIS] has_story_points={has_story_points} "
                f"(stats={has_story_points_in_stats}, bugs={has_story_points_in_bugs}), "
                f"weekly_stats count={len(weekly_stats)}"
            )
            if weekly_stats:
                logger.debug(f"[BUG ANALYSIS] Sample stat: {weekly_stats[0]}")

            # Bug Investment Chart - only show when points tracking is enabled AND has data
            if show_points and has_points_data and has_story_points:
                investment_chart = BugInvestmentChart(
                    weekly_stats, viewport_size="mobile"
                )
            elif not show_points:
                # Points tracking disabled
                investment_chart = dbc.Card(
                    dbc.CardBody(
                        [
                            html.H5(
                                "Bug Investment Chart",
                                className="card-title mb-3",
                            ),
                            html.Div(
                                [
                                    html.I(
                                        className="fas fa-toggle-off fa-lg text-secondary"
                                    ),
                                    html.Div(
                                        "Points Tracking Disabled",
                                        className="fw-bold",
                                        style={
                                            "fontSize": "1rem",
                                            "color": "#6c757d",
                                        },
                                    ),
                                    html.Small(
                                        "Enable points tracking in Settings to view bug investment by story points.",
                                        className="text-muted",
                                        style={"fontSize": "0.85rem"},
                                    ),
                                ],
                                className="d-flex align-items-center justify-content-center flex-column",
                                style={"gap": "0.25rem"},
                            ),
                        ],
                    ),
                    className="mb-3",
                    style={
                        "borderRadius": "0.375rem",
                        "border": "1px solid #dee2e6",
                        "backgroundColor": "#f8f9fa",
                    },
                )
            else:
                # Points tracking enabled but no data in filtered period
                investment_chart = dbc.Card(
                    dbc.CardBody(
                        [
                            html.H5(
                                "Bug Investment Chart",
                                className="card-title mb-3",
                            ),
                            html.Div(
                                [
                                    html.I(
                                        className="fas fa-database fa-lg text-secondary"
                                    ),
                                    html.Div(
                                        "No Points Data",
                                        className="fw-bold",
                                        style={
                                            "fontSize": "1rem",
                                            "color": "#6c757d",
                                        },
                                    ),
                                    html.Small(
                                        "No story points data available in the selected time period. Configure story points field in Settings or complete bug items with point estimates.",
                                        className="text-muted",
                                        style={"fontSize": "0.85rem"},
                                    ),
                                ],
                                className="d-flex align-items-center justify-content-center flex-column",
                                style={"gap": "0.25rem"},
                            ),
                        ],
                    ),
                    className="mb-3",
                    style={
                        "borderRadius": "0.375rem",
                        "border": "1px solid #dee2e6",
                        "backgroundColor": "#f8f9fa",
                    },
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
                all_bug_issues,
                timeline_filtered_bugs,
                weekly_stats=[],
                date_from=date_from,
                date_to=date_to,
                all_project_issues=all_issues,
            )
            # Create empty forecast for insufficient data
            forecast = {"insufficient_data": True}
            metrics_cards = create_bug_metrics_cards(bug_metrics, forecast)

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
        # Wrap in div with ID for fade-in animation
        return html.Div(
            dbc.Container(
                [
                    # Combined bug metrics cards (Resolution Rate + Open Bugs + Expected Resolution)
                    dbc.Row([dbc.Col([metrics_cards], width=12)], className="mb-4"),
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
                                        generate_quality_insights(
                                            bug_metrics, weekly_stats
                                        ),
                                        weekly_stats=weekly_stats,
                                    )
                                ],
                                width=12,
                            )
                        ]
                    ),
                ],
                fluid=True,
                className="py-4",
            ),
            id="bug-analysis-tab-content",
        )

    except Exception as e:
        logger.error(f"Error updating bug metrics: {e}", exc_info=True)
        # Return complete error page (not just error cards)
        # Wrap in div with ID for fade-in animation
        return html.Div(
            [
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
            ],
            id="bug-analysis-tab-content",
        )


#######################################################################
# MODULE REGISTRATION
#######################################################################


def register(app):
    """
    Register bug analysis callbacks with the app.

    Note: Bug analysis no longer uses a separate callback - content is
    rendered directly in the visualization callback for instant loading.
    This function exists for compatibility with the callback registration pattern.
    """
    logger.info("Bug analysis rendering function registered (no callbacks needed)")
    pass


#######################################################################
# MODULE EXPORTS
#######################################################################

# Export the rendering function for use by visualization callback
__all__ = ["_render_bug_analysis_content", "register"]
