import logging
from datetime import datetime, timedelta
from typing import Any

from dash import Input, Output, State, callback, html, no_update

from configuration.help_content_metrics import FLOW_METRICS_TOOLTIPS
from data.dora_forecast import calculate_dynamic_forecast
from data.metrics.blending import calculate_current_week_blend, get_blend_metadata
from data.metrics_calculator import calculate_flow_load_range, calculate_forecast
from data.metrics_snapshots import (
    get_available_weeks,
    get_metric_snapshot,
    get_metric_weekly_values,
)
from data.persistence import load_app_settings
from data.time_period_calculator import format_year_week, get_iso_week
from ui.empty_states import create_no_data_state, create_no_metrics_state
from ui.flow_metrics_dashboard import (
    _get_flow_performance_tier,
    _get_flow_performance_tier_color,
)
from ui.loading_utils import create_skeleton_loader
from ui.metric_cards import create_metric_cards_grid
from ui.work_distribution_card import create_work_distribution_card

logger = logging.getLogger(__name__)


@callback(
    [
        Output("flow-metrics-cards-container", "children"),
        Output("flow-metrics-store", "data"),
    ],
    [
        Input("jira-issues-store", "data"),
        Input("chart-tabs", "active_tab"),
        Input("data-points-input", "value"),
        Input("metrics-refresh-trigger", "data"),
    ],
    [
        State("current-settings", "data"),
    ],
    prevent_initial_call=False,
)
def calculate_and_display_flow_metrics(
    jira_data_store: dict[str, Any] | None,
    active_tab: str | None,
    data_points: int,
    metrics_refresh_trigger: int | None,
    app_settings: dict[str, Any] | None,
):

    try:
        import dash_bootstrap_components as dbc  # noqa: PLC0415

        logger.info(
            f"FLOW CALLBACK START: jira_data_store type={type(jira_data_store)}"
        )
        logger.info(
            f"FLOW CALLBACK START: jira_data_store is None = {jira_data_store is None}"
        )
        logger.info(
            f"FLOW CALLBACK START: bool(jira_data_store) = {bool(jira_data_store)}"
        )
        logger.info(f"FLOW CALLBACK START: active_tab = {active_tab}")
        if jira_data_store is not None:
            keys_info = (
                jira_data_store.keys()
                if isinstance(jira_data_store, dict)
                else "NOT A DICT"
            )
            logger.info(f"FLOW CALLBACK START: jira_data_store.keys() = {keys_info}")
            if isinstance(jira_data_store, dict):
                issues_count = len(jira_data_store.get("issues", []))
                logger.info(f"FLOW CALLBACK START: len(issues) = {issues_count}")

        if active_tab != "tab-flow-metrics":
            logger.info("FLOW: Not on Flow tab, skipping render")
            return no_update, no_update

        if jira_data_store is None or not jira_data_store:
            logger.info("Flow: Initial load, showing skeleton cards")
            return (
                dbc.Row(
                    [
                        dbc.Col(
                            create_skeleton_loader(type="card", height="200px"),
                            xs=12,
                            sm=6,
                            lg=3,
                            className="mb-4",
                        )
                        for _ in range(4)
                    ],
                    className="g-4",
                ),
                {},
            )

        if not jira_data_store.get("issues"):
            return create_no_data_state(), {}

        if not app_settings:
            logger.warning("No app settings available, loading from disk")
            app_settings = load_app_settings()

        if not app_settings:
            error_msg = "Failed to load app settings"
            logger.error(error_msg)
            return html.Div(error_msg, className="alert alert-danger p-4"), {}

        n_weeks = data_points if data_points and data_points > 0 else 12

        weeks = []
        current_date = datetime.now()
        for _ in range(n_weeks):
            year, week = get_iso_week(current_date)
            week_label = format_year_week(year, week)
            weeks.append(week_label)
            current_date = current_date - timedelta(days=7)

        week_labels = list(reversed(weeks))
        current_week_label = week_labels[-1] if week_labels else ""

        logger.info(
            f"Flow: Reading snapshots for {len(week_labels)} weeks: "
            f"{week_labels[:3]}...{week_labels[-3:]}"
        )

        available_weeks = get_available_weeks()
        has_any_data = any(week in available_weeks for week in week_labels)

        if not has_any_data:
            logger.warning(
                "No Flow metrics snapshots found for any of "
                f"the {len(week_labels)} weeks"
            )

            return create_no_metrics_state(metric_type="Flow"), {}

        flow_load_values = get_metric_weekly_values(
            week_labels, "flow_load", "wip_count"
        )
        flow_time_values = get_metric_weekly_values(
            week_labels, "flow_time", "median_days"
        )
        flow_efficiency_values = get_metric_weekly_values(
            week_labels, "flow_efficiency", "overall_pct"
        )
        velocity_values = get_metric_weekly_values(
            week_labels, "flow_velocity", "completed_count"
        )

        velocity_values_adjusted = None
        blend_metadata = None
        if velocity_values and len(velocity_values) >= 2:
            current_week_actual = velocity_values[-1]

            prior_weeks = velocity_values[:-1]
            forecast_weeks = prior_weeks[-4:] if len(prior_weeks) >= 4 else prior_weeks

            forecast_data = None
            forecast_value = 0
            if len(forecast_weeks) >= 2:
                try:
                    forecast_data = calculate_forecast(forecast_weeks)
                    forecast_value = (
                        forecast_data.get("forecast_value", 0) if forecast_data else 0
                    )
                except Exception as e:
                    logger.warning(f"Failed to calculate velocity forecast: {e}")

            if forecast_value > 0:
                blended_value = calculate_current_week_blend(
                    current_week_actual, forecast_value
                )

                blend_metadata = get_blend_metadata(current_week_actual, forecast_value)

                velocity_values_adjusted = list(velocity_values)
                velocity_values_adjusted[-1] = blended_value

                logger.info(
                    f"[Blending] Flow Velocity - Actual: {current_week_actual:.1f}, "
                    f"Forecast: {forecast_value:.1f}, "
                    f"Blended: {blended_value:.1f} "
                    f"({blend_metadata['actual_percent']:.0f}% actual, "
                    f"{blend_metadata['forecast_percent']:.0f}% forecast "
                    f"on {blend_metadata['day_name']})"
                )
            else:
                logger.debug("[Blending] Skipped - insufficient forecast data")

        flow_time_values_adjusted = None
        flow_time_blend_metadata = None
        if flow_time_values and len(flow_time_values) >= 2:
            current_week_actual = flow_time_values[-1]
            prior_weeks = [v for v in flow_time_values[:-1] if v > 0]
            forecast_weeks = prior_weeks[-4:] if len(prior_weeks) >= 4 else prior_weeks

            if len(forecast_weeks) >= 2:
                try:
                    forecast_data = calculate_forecast(forecast_weeks)
                    forecast_value = (
                        forecast_data.get("forecast_value", 0) if forecast_data else 0
                    )

                    if forecast_value > 0:
                        blended_value = calculate_current_week_blend(
                            current_week_actual, forecast_value
                        )
                        flow_time_blend_metadata = get_blend_metadata(
                            current_week_actual, forecast_value
                        )
                        flow_time_values_adjusted = list(flow_time_values)
                        flow_time_values_adjusted[-1] = blended_value

                        logger.info(
                            "[Blending] Flow Time - "
                            f"Actual: {current_week_actual:.1f}, "
                            f"Forecast: {forecast_value:.1f}, "
                            f"Blended: {blended_value:.1f}"
                        )
                except Exception as e:
                    logger.warning(f"Failed to blend flow time: {e}")

        velocity_values_for_calc = velocity_values_adjusted or velocity_values
        avg_velocity = (
            sum(velocity_values_for_calc) / len(velocity_values_for_calc)
            if velocity_values_for_calc
            else 0
        )

        flow_time_values_for_calc = flow_time_values_adjusted or flow_time_values
        non_zero_flow_times = [v for v in flow_time_values_for_calc if v > 0]
        if non_zero_flow_times:
            sorted_times = sorted(non_zero_flow_times)
            mid = len(sorted_times) // 2
            median_flow_time = (
                sorted_times[mid]
                if len(sorted_times) % 2 == 1
                else (sorted_times[mid - 1] + sorted_times[mid]) / 2
            )
        else:
            median_flow_time = 0

        non_zero_efficiency = [v for v in flow_efficiency_values if v > 0]
        avg_efficiency = (
            sum(non_zero_efficiency) / len(non_zero_efficiency)
            if non_zero_efficiency
            else 0
        )

        flow_load_snapshot = get_metric_snapshot(current_week_label, "flow_load")
        if not flow_load_snapshot and available_weeks:
            for week in week_labels[::-1]:
                flow_load_snapshot = get_metric_snapshot(week, "flow_load")
                if flow_load_snapshot:
                    logger.info(
                        f"Flow: Using WIP data from {week} "
                        f"(current week {current_week_label} not available)"
                    )
                    break
        wip_count = flow_load_snapshot.get("wip_count", 0) if flow_load_snapshot else 0

        total_feature = 0
        total_defect = 0
        total_tech_debt = 0
        total_risk = 0
        total_completed = 0
        distribution_history = []

        for week in week_labels:
            week_snapshot = get_metric_snapshot(week, "flow_velocity")
            if week_snapshot:
                week_dist = week_snapshot.get("distribution", {})
                week_feature = week_dist.get("feature", 0)
                week_defect = week_dist.get("defect", 0)
                week_tech_debt = week_dist.get("tech_debt", 0)
                week_risk = week_dist.get("risk", 0)
                week_total = week_snapshot.get("completed_count", 0)

                total_feature += week_feature
                total_defect += week_defect
                total_tech_debt += week_tech_debt
                total_risk += week_risk
                total_completed += week_total

                distribution_history.append(
                    {
                        "week": week,
                        "feature": week_feature,
                        "defect": week_defect,
                        "tech_debt": week_tech_debt,
                        "risk": week_risk,
                        "total": week_total,
                    }
                )
            else:
                distribution_history.append(
                    {
                        "week": week,
                        "feature": 0,
                        "defect": 0,
                        "tech_debt": 0,
                        "risk": 0,
                        "total": 0,
                    }
                )

        feature_count = total_feature
        defect_count = total_defect
        tech_debt_count = total_tech_debt
        risk_count = total_risk
        total_velocity = total_completed
        issues_in_period_count = total_completed

        logger.info(
            f"Flow metrics AGGREGATED over {n_weeks} weeks: "
            f"Velocity={avg_velocity:.2f} items/week (total {total_completed}), "
            f"Flow Time={median_flow_time:.2f}d (median), "
            f"Efficiency={avg_efficiency:.2f}% (avg), "
            f"WIP={wip_count} (current week {current_week_label})"
        )

        distribution_data = {
            "feature": feature_count,
            "defect": defect_count,
            "tech_debt": tech_debt_count,
            "risk": risk_count,
            "total": total_velocity,
        }

        dist_card = create_work_distribution_card(
            distribution_data=distribution_data,
            week_label=f"{n_weeks} weeks aggregate",
            distribution_history=distribution_history,
            card_id="work-distribution-card",
        )

        metrics_data = {
            "flow_velocity": {
                "metric_name": "flow_velocity",
                "value": avg_velocity,
                "_n_weeks": n_weeks,
                "unit": "items/week",
                "error_state": "success"
                if avg_velocity > 0 or issues_in_period_count > 0
                else "no_data",
                "performance_tier": _get_flow_performance_tier(
                    "flow_velocity", avg_velocity
                ),
                "performance_tier_color": _get_flow_performance_tier_color(
                    "flow_velocity", avg_velocity
                ),
                "total_issue_count": issues_in_period_count,
                "weekly_labels": week_labels,
                "weekly_values": velocity_values,
                "weekly_values_adjusted": velocity_values_adjusted,
                "blend_metadata": blend_metadata,
                "details": {
                    "Feature": feature_count,
                    "Defect": defect_count,
                    "Technical Debt": tech_debt_count,
                    "Risk": risk_count,
                },
            },
            "flow_time": {
                "metric_name": "flow_time",
                "value": median_flow_time if median_flow_time is not None else 0,
                "_n_weeks": n_weeks,
                "unit": "days",
                "error_state": "success"
                if median_flow_time > 0 or issues_in_period_count > 0
                else "no_data",
                "performance_tier": _get_flow_performance_tier(
                    "flow_time", median_flow_time if median_flow_time is not None else 0
                ),
                "performance_tier_color": _get_flow_performance_tier_color(
                    "flow_time", median_flow_time if median_flow_time is not None else 0
                ),
                "total_issue_count": issues_in_period_count,
                "weekly_labels": week_labels,
                "weekly_values": flow_time_values,
                "weekly_values_adjusted": flow_time_values_adjusted,
                "blend_metadata": flow_time_blend_metadata,
            },
            "flow_efficiency": {
                "metric_name": "flow_efficiency",
                "value": avg_efficiency if avg_efficiency is not None else 0,
                "_n_weeks": n_weeks,
                "unit": "%",
                "error_state": "success"
                if avg_efficiency > 0 or issues_in_period_count > 0
                else "no_data",
                "performance_tier": _get_flow_performance_tier(
                    "flow_efficiency",
                    avg_efficiency if avg_efficiency is not None else 0,
                ),
                "performance_tier_color": _get_flow_performance_tier_color(
                    "flow_efficiency",
                    avg_efficiency if avg_efficiency is not None else 0,
                ),
                "total_issue_count": issues_in_period_count,
                "weekly_labels": week_labels,
                "weekly_values": flow_efficiency_values,
            },
            "flow_load": {
                "metric_name": "flow_load",
                "value": wip_count if wip_count is not None else 0,
                "_n_weeks": n_weeks,
                "unit": "items",
                "error_state": "success" if flow_load_snapshot else "no_data",
                "performance_tier": _get_flow_performance_tier(
                    "flow_load", wip_count if wip_count is not None else 0
                ),
                "performance_tier_color": _get_flow_performance_tier_color(
                    "flow_load", wip_count if wip_count is not None else 0
                ),
                "total_issue_count": wip_count,
                "weekly_labels": week_labels,
                "weekly_values": flow_load_values,
            },
        }

        logger.info(
            f"FLOW: Calculating dynamic forecasts for {data_points} weeks of data"
        )

        flow_metric_types = {
            "flow_velocity": "higher_better",
            "flow_time": "lower_better",
            "flow_efficiency": "higher_better",
            "flow_load": "lower_better",
        }

        for metric_name in [
            "flow_velocity",
            "flow_time",
            "flow_efficiency",
            "flow_load",
        ]:
            weekly_values = metrics_data[metric_name].get("weekly_values", [])
            current_value = metrics_data[metric_name].get("value")
            metric_type = flow_metric_types.get(metric_name, "higher_better")

            forecast_data, trend_vs_forecast = calculate_dynamic_forecast(
                weekly_values=weekly_values,
                current_value=current_value,
                metric_type=metric_type,
                metric_name=metric_name,
            )

            if forecast_data:
                metrics_data[metric_name]["forecast_data"] = forecast_data

                if metric_name == "flow_load":
                    try:
                        FLOW_LOAD_RANGE_PERCENT = 0.20
                        range_data = calculate_flow_load_range(
                            forecast_value=forecast_data["forecast_value"],
                            range_percent=FLOW_LOAD_RANGE_PERCENT,
                        )
                        forecast_data["forecast_range"] = range_data
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Failed to calculate Flow Load range: {e}")

            if trend_vs_forecast:
                metrics_data[metric_name]["trend_vs_forecast"] = trend_vs_forecast

        metrics_html = create_metric_cards_grid(
            metrics_data, tooltips=FLOW_METRICS_TOOLTIPS
        )

        dist_col = dbc.Col(dist_card, xs=12, lg=12, className="mb-3")
        if metrics_html and metrics_html.children:
            metrics_html.children.append(dist_col)

        return metrics_html, metrics_data

    except Exception as e:
        logger.error(f"Error calculating Flow metrics: {e}", exc_info=True)

        return html.Div("Error loading metrics", className="alert alert-danger p-4"), {}
