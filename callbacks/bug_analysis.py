import logging
from datetime import datetime, timedelta

import dash_bootstrap_components as dbc
from dash import html

from configuration.settings import get_bug_analysis_config
from data.bug_insights import generate_quality_insights
from data.bug_processing import (
    calculate_bug_metrics_summary,
    calculate_bug_statistics,
    filter_bug_issues,
    forecast_bug_resolution,
)
from data.issue_filtering import filter_issues_for_metrics
from data.persistence import load_app_settings, load_jira_configuration
from data.persistence.factory import get_backend
from ui.bug_analysis import (
    create_bug_metrics_cards,
    create_quality_insights_panel,
)
from ui.bug_charts import BugInvestmentChart, BugTrendChart
from ui.empty_states import create_no_bugs_state
from ui.loading_utils import create_content_placeholder

logger = logging.getLogger(__name__)


def _render_bug_analysis_content(
    data_points_count: int, show_points: bool = True, has_points_data: bool = False
):

    logger.info(f"Rendering bug analysis content with data_points: {data_points_count}")

    try:
        bug_config = get_bug_analysis_config()

        jira_config = load_jira_configuration()
        points_field = jira_config.get("points_field", "")

        all_issues = []

        try:
            backend = get_backend()
            active_profile_id = backend.get_app_state("active_profile_id")
            active_query_id = backend.get_app_state("active_query_id")

            if active_profile_id and active_query_id:
                all_issues = backend.get_issues(active_profile_id, active_query_id)

                if all_issues:
                    logger.debug(
                        f"Loaded {len(all_issues)} issues from database for "
                        f"{active_profile_id}/{active_query_id}"
                    )
                else:
                    logger.warning(
                        "No issues found in database for "
                        f"{active_profile_id}/{active_query_id}"
                    )
            else:
                logger.warning(
                    "No active profile/query configured: "
                    f"profile_id={active_profile_id}, "
                    f"query_id={active_query_id}"
                )
        except Exception as e:
            logger.warning(f"Could not load from JIRA cache: {e}")

        if all_issues:
            settings = load_app_settings()

            original_count = len(all_issues)
            all_issues = filter_issues_for_metrics(
                all_issues, settings=settings, log_prefix="BUG ANALYSIS"
            )
            filtered_count = original_count - len(all_issues)
            if filtered_count > 0:
                logger.info(
                    "Bug Analysis: Filtered to "
                    f"{len(all_issues)} development project issues "
                    f"from {original_count} total"
                )

        date_to = datetime.now()
        date_from = date_to - timedelta(weeks=data_points_count or 12)

        all_bug_issues = filter_bug_issues(
            all_issues,
            bug_type_mappings=bug_config.get("issue_type_mappings", {}),
            date_from=None,
            date_to=None,
        )

        timeline_filtered_bugs = filter_bug_issues(
            all_issues,
            bug_type_mappings=bug_config.get("issue_type_mappings", {}),
            date_from=date_from,
            date_to=date_to,
        )

        logger.info(
            f"Total bug issues: {len(all_bug_issues)} (all time), "
            f"{len(timeline_filtered_bugs)} in selected timeline "
            "(date range: "
            f"{date_from.date()} to {date_to.date()}, "
            f"{data_points_count} weeks)"
        )

        if len(all_bug_issues) == 0:
            return html.Div(
                dbc.Container(
                    create_no_bugs_state(),
                    fluid=True,
                    className="py-4",
                ),
                id="bug-analysis-tab-content",
            )

        weekly_stats = []

        if len(timeline_filtered_bugs) == 0 and len(all_bug_issues) > 0:
            return html.Div(
                create_content_placeholder(
                    type="chart",
                    text=(
                        "No bug data in selected timeframe. "
                        f"Found {len(all_bug_issues)} total bugs, "
                        f"but none in the last {data_points_count} weeks. "
                        "Use the Data Points slider in Settings "
                        "to expand the timeline."
                    ),
                    icon="fa-calendar-times",
                    height="400px",
                ),
                id="bug-analysis-tab-content",
            )

        try:
            logger.info(
                "Attempting to calculate statistics with "
                f"{len(timeline_filtered_bugs)} bugs "
                f"from {date_from} to {date_to}"
            )

            weekly_stats = calculate_bug_statistics(
                timeline_filtered_bugs,
                date_from,
                date_to,
                story_points_field=points_field,
            )

            logger.info(
                f"Successfully calculated {len(weekly_stats)} weeks of statistics"
            )

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

            forecast = forecast_bug_resolution(
                bug_metrics.get("open_bugs", 0),
                weekly_stats,
                use_last_n_weeks=8,
            )

            metrics_cards = create_bug_metrics_cards(bug_metrics, forecast)

            trends_chart = BugTrendChart(weekly_stats, viewport_size="mobile")

            has_story_points_in_stats = any(
                stat.get("bugs_points_created", 0) > 0
                or stat.get("bugs_points_resolved", 0) > 0
                for stat in weekly_stats
            )

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
                "(stats="
                f"{has_story_points_in_stats}, bugs={has_story_points_in_bugs}), "
                f"weekly_stats count={len(weekly_stats)}"
            )
            if weekly_stats:
                logger.debug(f"[BUG ANALYSIS] Sample stat: {weekly_stats[0]}")

            if show_points and has_points_data and has_story_points:
                investment_chart = BugInvestmentChart(
                    weekly_stats, viewport_size="mobile"
                )
            elif not show_points:
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
                                        className=(
                                            "fas fa-toggle-off fa-lg text-secondary"
                                        )
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
                                        "Enable points tracking in Settings "
                                        "to view bug investment by story points.",
                                        className="text-muted",
                                        style={"fontSize": "0.85rem"},
                                    ),
                                ],
                                className=(
                                    "d-flex align-items-center "
                                    "justify-content-center flex-column"
                                ),
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
                                        "No story points data available in the "
                                        "selected time period. Configure story "
                                        "points field in Settings or complete bug "
                                        "items with point estimates.",
                                        className="text-muted",
                                        style={"fontSize": "0.85rem"},
                                    ),
                                ],
                                className=(
                                    "d-flex align-items-center "
                                    "justify-content-center flex-column"
                                ),
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
            logger.error(f"Could not calculate bug statistics: {ve}")
            logger.error(
                f"Bug count: {len(timeline_filtered_bugs)}, "
                f"date_from: {date_from}, date_to: {date_to}"
            )
            weekly_stats = []

            bug_metrics = calculate_bug_metrics_summary(
                all_bug_issues,
                timeline_filtered_bugs,
                weekly_stats=[],
                date_from=date_from,
                date_to=date_to,
                all_project_issues=all_issues,
            )
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

        return html.Div(
            dbc.Container(
                [
                    dbc.Row([dbc.Col([metrics_cards], width=12)], className="mb-4"),
                    dbc.Row([dbc.Col([trends_chart], width=12)], className="mb-4"),
                    dbc.Row([dbc.Col([investment_chart], width=12)], className="mb-4"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
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
                                                className=(
                                                    "fas fa-exclamation-triangle me-2"
                                                )
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


def register(app):

    logger.info("Bug analysis rendering function registered (no callbacks needed)")
    pass


__all__ = ["_render_bug_analysis_content", "register"]
