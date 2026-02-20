"""Metrics refresh callbacks for Flow and DORA calculations."""

import logging
from datetime import datetime

from dash import Input, Output, State, callback, html

logger = logging.getLogger(__name__)


#######################################################################
# REFRESH METRICS CALLBACK
#######################################################################


@callback(
    [
        Output("calculate-metrics-status", "children"),
        Output("calculate-metrics-button", "disabled"),
        Output("calculate-metrics-button", "children"),
        Output("metrics-refresh-trigger", "data"),
    ],
    [Input("calculate-metrics-button", "n_clicks")],
    [State("data-points-input", "value")],
    prevent_initial_call=False,
)
def calculate_metrics_from_settings(
    button_clicks: int | None,
    data_points: int | None,
):
    """Calculate Flow and DORA metrics from Settings panel button."""
    logger.info(
        f"[CALCULATE METRICS] Callback triggered - button_clicks={button_clicks}"
    )

    if not button_clicks:
        return (
            "",
            False,
            [
                html.I(className="fas fa-calculator", style={"marginRight": "0.5rem"}),
                "Calculate Metrics",
            ],
            None,
        )

    try:
        logger.info("Starting Flow metrics calculation from Settings panel")

        from datetime import timedelta

        from data.iso_week_bucketing import get_iso_week_bounds, get_week_label
        from data.jira import get_jira_config, load_jira_cache
        from data.task_progress import TaskProgress

        weeks_to_calculate = []
        try:
            config = get_jira_config()
            cache_loaded, cached_issues = load_jira_cache(
                current_jql_query="",
                current_fields="created,resolutiondate",
                config=config,
            )

            if cache_loaded and cached_issues:
                all_dates = []
                for issue in cached_issues:
                    fields = issue.get("fields", {})

                    for field_name in ["created", "resolutiondate"]:
                        date_str = fields.get(field_name)
                        if date_str:
                            try:
                                all_dates.append(
                                    datetime.fromisoformat(
                                        date_str.replace("Z", "+00:00")
                                    )
                                )
                            except (ValueError, AttributeError):
                                pass

                if all_dates:
                    all_dates.sort()
                    earliest_date = all_dates[0]
                    latest_date = all_dates[-1]

                    logger.info(
                        f"Data range: {earliest_date.date()} to {latest_date.date()}"
                    )

                    current = earliest_date
                    while current <= latest_date:
                        monday, sunday = get_iso_week_bounds(current)
                        week_label = get_week_label(current)
                        weeks_to_calculate.append((week_label, monday, sunday))
                        current = current + timedelta(days=7)

                    seen_labels = set()
                    unique_weeks = []
                    for week_label, monday, sunday in weeks_to_calculate:
                        if week_label not in seen_labels:
                            seen_labels.add(week_label)
                            unique_weeks.append((week_label, monday, sunday))

                    weeks_to_calculate = unique_weeks
                    n_weeks = len(weeks_to_calculate)

                    logger.info(
                        f"Calculated {n_weeks} weeks from data range "
                        f"({earliest_date.date()} to {latest_date.date()})"
                    )
                else:
                    logger.warning(
                        "No dates found in cache, falling back to 52 weeks from today"
                    )
                    weeks_to_calculate = None
                    n_weeks = 52
            else:
                logger.warning("Cache not loaded, falling back to 52 weeks from today")
                weeks_to_calculate = None
                n_weeks = 52
        except Exception as e:
            logger.error(f"Error detecting data range: {e}", exc_info=True)
            weeks_to_calculate = None
            n_weeks = 52

        logger.info(
            f"Calculating metrics for {n_weeks} weeks based on actual data range. "
            f"Data Points slider ({data_points}) controls display only."
        )

        TaskProgress.start_task(
            "calculate_metrics",
            f"Calculating {n_weeks} weeks of metrics",
            weeks=n_weeks,
        )

        from data.metrics_calculator import calculate_metrics_for_last_n_weeks

        if weeks_to_calculate:
            success, message = calculate_metrics_for_last_n_weeks(
                n_weeks=n_weeks, custom_weeks=weeks_to_calculate
            )
        else:
            success, message = calculate_metrics_for_last_n_weeks(n_weeks=n_weeks)

        if success:
            from data.iso_week_bucketing import get_week_label
            from data.metrics_snapshots import add_forecasts_to_week

            current_week_label = get_week_label(datetime.now())
            logger.info(
                "Adding forecasts to week "
                f"{current_week_label} after metrics calculation"
            )

            forecast_success = add_forecasts_to_week(current_week_label)
            if forecast_success:
                logger.info(f"Successfully added forecasts to {current_week_label}")
            else:
                logger.warning(f"Failed to add forecasts to {current_week_label}")

        TaskProgress.complete_task("calculate_metrics")

        button_normal = [
            html.I(className="fas fa-calculator", style={"marginRight": "0.5rem"}),
            "Calculate Metrics",
        ]

        actual_weeks_processed = n_weeks
        if "calculated metrics for all" in message.lower():
            import re

            match = re.search(r"all (\d+) weeks", message)
            if match:
                actual_weeks_processed = int(match.group(1))
        elif "calculated metrics for" in message.lower():
            import re

            match = re.search(r"for (\d+)/(\d+) weeks", message)
            if match:
                actual_weeks_processed = int(match.group(1))

        if success:
            settings_status_html = html.Div(
                [
                    html.I(className="fas fa-check-circle me-2 text-success"),
                    html.Span(
                        f"Calculated {actual_weeks_processed} weeks "
                        "of Flow & DORA metrics",
                        className="fw-medium",
                    ),
                ],
                className="text-success small text-center mt-2",
            )

            logger.info(
                "Flow & DORA metrics calculation completed successfully: "
                f"{actual_weeks_processed} weeks processed "
                f"(requested {n_weeks})"
            )

            refresh_timestamp = datetime.now().isoformat()
            return settings_status_html, False, button_normal, refresh_timestamp

        settings_status_html = html.Div(
            [
                html.I(className="fas fa-exclamation-triangle me-2 text-warning"),
                html.Span(
                    "Metrics calculated with warnings (check logs)",
                    className="fw-medium",
                ),
            ],
            className="text-warning small text-center mt-2",
        )

        logger.warning("Flow & DORA metrics calculation had issues")

        refresh_timestamp = datetime.now().isoformat()
        return settings_status_html, False, button_normal, refresh_timestamp

    except Exception as e:
        from data.task_progress import TaskProgress

        TaskProgress.complete_task("calculate_metrics")

        error_msg = f"Error calculating metrics: {str(e)}"
        logger.error(error_msg, exc_info=True)

        settings_status_html = html.Div(
            [
                html.I(className="fas fa-times-circle me-2 text-danger"),
                html.Span(
                    f"Calculation failed: {str(e)[:50]}",
                    className="fw-medium",
                ),
            ],
            className="text-danger small text-center mt-2",
        )

        button_normal = [
            html.I(className="fas fa-calculator", style={"marginRight": "0.5rem"}),
            "Calculate Metrics",
        ]

        return settings_status_html, False, button_normal, None
