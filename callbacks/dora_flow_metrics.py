"""DORA metrics dashboard callbacks."""

import logging
from typing import Any

from dash import Input, Output, callback
from dash.exceptions import PreventUpdate

from configuration.help_content import DORA_METRICS_TOOLTIPS
from data.dora_forecast import calculate_dynamic_forecast
from data.dora_metrics_blending import calculate_dora_blended_series
from ui.metric_cards import create_metric_cards_grid

logger = logging.getLogger(__name__)


#######################################################################
# DORA METRICS CALLBACK
#######################################################################


@callback(
    [
        Output("dora-metrics-cards-container", "children"),
        Output("dora-metrics-store", "data"),
    ],
    [
        Input("jira-issues-store", "data"),
        Input("chart-tabs", "active_tab"),
        Input("data-points-input", "value"),
        Input("metrics-refresh-trigger", "data"),
    ],
    prevent_initial_call=False,
)
def load_and_display_dora_metrics(
    jira_data_store: dict[str, Any] | None,
    active_tab: str | None,
    data_points: int,
    refresh_trigger: Any | None,
):
    """Load and display DORA metrics from cache."""
    try:
        import dash_bootstrap_components as dbc

        from ui.loading_utils import create_skeleton_loader

        logger.info(
            f"DORA CALLBACK START: jira_data_store type={type(jira_data_store)}"
        )
        logger.info(
            f"DORA CALLBACK START: jira_data_store is None = {jira_data_store is None}"
        )
        logger.info(
            f"DORA CALLBACK START: bool(jira_data_store) = {bool(jira_data_store)}"
        )
        logger.info(f"DORA CALLBACK START: active_tab = {active_tab}")
        if jira_data_store is not None:
            keys_info = (
                jira_data_store.keys()
                if isinstance(jira_data_store, dict)
                else "NOT A DICT"
            )
            logger.info(f"DORA CALLBACK START: jira_data_store.keys() = {keys_info}")
            if isinstance(jira_data_store, dict):
                issues_count = len(jira_data_store.get("issues", []))
                logger.info(f"DORA CALLBACK START: len(issues) = {issues_count}")

        if active_tab != "tab-dora-metrics":
            from dash import no_update

            logger.info("DORA: Not on DORA tab, skipping render")
            return no_update, no_update

        if jira_data_store is None or not jira_data_store:
            logger.info("DORA: Initial load, showing skeleton cards")
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
            from ui.empty_states import create_no_data_state

            logger.info("DORA: No JIRA issues in loaded data, showing 'No Data' state")
            return create_no_data_state(), {}

        n_weeks = data_points if data_points and data_points > 0 else 12

        from data.dora_metrics_calculator import load_dora_metrics_from_cache

        logger.info(f"DORA: Loading metrics from cache for {n_weeks} weeks")
        cached_metrics = load_dora_metrics_from_cache(n_weeks=n_weeks)

        if cached_metrics:
            cached_metrics["_n_weeks"] = n_weeks

        logger.info("===== DORA METRICS DEBUG =====")
        logger.info(f"cached_metrics type: {type(cached_metrics)}")
        logger.info(f"cached_metrics is None: {cached_metrics is None}")
        logger.info(f"cached_metrics bool: {bool(cached_metrics)}")
        if cached_metrics:
            logger.info(f"cached_metrics keys: {list(cached_metrics.keys())}")
            for key, val in cached_metrics.items():
                if isinstance(val, dict):
                    metric_value = val.get("value")
                    labels_count = len(val.get("weekly_labels", []))
                    logger.info(f"  {key}: value={metric_value}, labels={labels_count}")
                else:
                    logger.info(f"  {key}: {val}")
        logger.info("===== END DEBUG =====")

        logger.info(
            f"DORA: Cache loaded, data is {'available' if cached_metrics else 'empty'}"
        )

        if not cached_metrics:
            from ui.empty_states import create_no_metrics_state

            return create_no_metrics_state(metric_type="DORA"), {}

        n_weeks_display = cached_metrics.get("_n_weeks", 12)

        blend_data = calculate_dora_blended_series(cached_metrics)
        deployment_weekly_values = blend_data["deployment_weekly_values"]
        deployment_weekly_values_adjusted = blend_data[
            "deployment_weekly_values_adjusted"
        ]
        deployment_blend_metadata = blend_data["deployment_blend_metadata"]
        lead_time_weekly_values = blend_data["lead_time_weekly_values"]
        lead_time_weekly_values_adjusted = blend_data[
            "lead_time_weekly_values_adjusted"
        ]
        lead_time_blend_metadata = blend_data["lead_time_blend_metadata"]
        mttr_weekly_values = blend_data["mttr_weekly_values"]
        mttr_weekly_values_adjusted = blend_data["mttr_weekly_values_adjusted"]
        mttr_blend_metadata = blend_data["mttr_blend_metadata"]

        from data.dora_metrics import (
            CHANGE_FAILURE_RATE_TIERS,
            DEPLOYMENT_FREQUENCY_TIERS,
            LEAD_TIME_TIERS,
            MTTR_TIERS,
            _determine_performance_tier,
        )

        deployment_weekly_values_for_calc = (
            deployment_weekly_values_adjusted or deployment_weekly_values
        )
        deployment_freq_value = (
            sum(deployment_weekly_values_for_calc)
            / len(deployment_weekly_values_for_calc)
            if deployment_weekly_values_for_calc
            else cached_metrics.get("deployment_frequency", {}).get("release_value", 0)
        )
        if deployment_freq_value == 0:
            deployment_freq_value = cached_metrics.get("deployment_frequency", {}).get(
                "value", 0
            )

        task_count_value = cached_metrics.get("deployment_frequency", {}).get(
            "value", 0
        )

        deployments_per_month = deployment_freq_value * 4.33

        deployment_freq_tier = _determine_performance_tier(
            deployments_per_month, DEPLOYMENT_FREQUENCY_TIERS
        )

        lead_time_value = cached_metrics.get("lead_time_for_changes", {}).get("value")
        lead_time_values_for_calc = (
            lead_time_weekly_values_adjusted or lead_time_weekly_values
        )
        if lead_time_values_for_calc:
            non_zero_values = [v for v in lead_time_values_for_calc if v > 0]
            if non_zero_values:
                lead_time_value = sum(non_zero_values) / len(non_zero_values)
        lead_time_tier = (
            _determine_performance_tier(lead_time_value, LEAD_TIME_TIERS)
            if lead_time_value is not None
            else {"tier": "Unknown", "color": "secondary"}
        )

        cfr_value = cached_metrics.get("change_failure_rate", {}).get("value", 0)
        cfr_tier = _determine_performance_tier(cfr_value, CHANGE_FAILURE_RATE_TIERS)

        mttr_value = cached_metrics.get("mean_time_to_recovery", {}).get("value")
        mttr_values_for_calc = mttr_weekly_values_adjusted or mttr_weekly_values
        if mttr_values_for_calc:
            non_zero_values = [v for v in mttr_values_for_calc if v > 0]
            if non_zero_values:
                mttr_value = sum(non_zero_values) / len(non_zero_values)
        mttr_tier = (
            _determine_performance_tier(mttr_value, MTTR_TIERS)
            if mttr_value is not None
            else {"tier": "Unknown", "color": "secondary"}
        )

        metrics_data = {
            "deployment_frequency": {
                "metric_name": "deployment_frequency",
                "value": deployment_freq_value,
                "task_value": task_count_value,
                "release_value": cached_metrics.get("deployment_frequency", {}).get(
                    "release_value", 0
                ),
                "_n_weeks": n_weeks_display,
                "unit": "releases/week",
                "error_state": "success" if deployment_freq_value > 0 else "no_data",
                "performance_tier": deployment_freq_tier["tier"],
                "performance_tier_color": deployment_freq_tier["color"],
                "total_issue_count": cached_metrics.get("deployment_frequency", {}).get(
                    "total_issue_count", 0
                ),
                "tooltip": (
                    f"{DORA_METRICS_TOOLTIPS.get('deployment_frequency', '')} "
                    f"Average calculated over last {n_weeks_display} weeks. "
                    "Shows unique releases (fixVersions) per week."
                ),
                "weekly_labels": cached_metrics.get("deployment_frequency", {}).get(
                    "weekly_labels", []
                ),
                "weekly_values": deployment_weekly_values,
                "weekly_values_adjusted": deployment_weekly_values_adjusted,
                "weekly_release_values": cached_metrics.get(
                    "deployment_frequency", {}
                ).get("weekly_release_values", []),
                "blend_metadata": deployment_blend_metadata,
            },
            "lead_time_for_changes": {
                "metric_name": "lead_time_for_changes",
                "value": lead_time_value,
                "value_hours": cached_metrics.get("lead_time_for_changes", {}).get(
                    "value_hours"
                ),
                "value_days": cached_metrics.get("lead_time_for_changes", {}).get(
                    "value_days"
                ),
                "p95_value": cached_metrics.get("lead_time_for_changes", {}).get(
                    "p95_value"
                ),
                "mean_value": cached_metrics.get("lead_time_for_changes", {}).get(
                    "mean_value"
                ),
                "_n_weeks": n_weeks_display,
                "unit": "days",
                "error_state": "success" if lead_time_value is not None else "no_data",
                "performance_tier": lead_time_tier["tier"],
                "performance_tier_color": lead_time_tier["color"],
                "total_issue_count": cached_metrics.get(
                    "lead_time_for_changes", {}
                ).get("total_issue_count", 0),
                "tooltip": (
                    f"{DORA_METRICS_TOOLTIPS.get('lead_time_for_changes', '')} "
                    f"Average calculated over last {n_weeks_display} weeks."
                ),
                "weekly_labels": cached_metrics.get("lead_time_for_changes", {}).get(
                    "weekly_labels", []
                ),
                "weekly_values": lead_time_weekly_values,
                "weekly_values_adjusted": lead_time_weekly_values_adjusted,
                "blend_metadata": lead_time_blend_metadata,
            },
            "change_failure_rate": {
                "metric_name": "change_failure_rate",
                "value": cached_metrics.get("change_failure_rate", {}).get("value", 0),
                "release_value": cached_metrics.get("change_failure_rate", {}).get(
                    "release_value", 0
                ),
                "_n_weeks": n_weeks_display,
                "unit": "%",
                "error_state": "success"
                if deployment_freq_value > 0 or task_count_value > 0
                else "no_data",
                "performance_tier": cfr_tier["tier"],
                "performance_tier_color": cfr_tier["color"],
                "total_issue_count": cached_metrics.get("change_failure_rate", {}).get(
                    "total_issue_count", 0
                ),
                "tooltip": (
                    f"{DORA_METRICS_TOOLTIPS.get('change_failure_rate', '')} "
                    f"Aggregate rate calculated over last {n_weeks_display} weeks. "
                    "Deployment-based vs Release-based rates."
                ),
                "weekly_labels": cached_metrics.get("change_failure_rate", {}).get(
                    "weekly_labels", []
                ),
                "weekly_values": cached_metrics.get("change_failure_rate", {}).get(
                    "weekly_values", []
                ),
                "weekly_release_values": cached_metrics.get(
                    "change_failure_rate", {}
                ).get("weekly_release_values", []),
            },
            "mean_time_to_recovery": {
                "metric_name": "mean_time_to_recovery",
                "value": mttr_value,
                "value_hours": cached_metrics.get("mean_time_to_recovery", {}).get(
                    "value_hours"
                ),
                "value_days": cached_metrics.get("mean_time_to_recovery", {}).get(
                    "value_days"
                ),
                "p95_value": cached_metrics.get("mean_time_to_recovery", {}).get(
                    "p95_value"
                ),
                "mean_value": cached_metrics.get("mean_time_to_recovery", {}).get(
                    "mean_value"
                ),
                "_n_weeks": n_weeks_display,
                "unit": "hours",
                "error_state": "success" if mttr_value is not None else "no_data",
                "performance_tier": mttr_tier["tier"],
                "performance_tier_color": mttr_tier["color"],
                "total_issue_count": cached_metrics.get(
                    "mean_time_to_recovery", {}
                ).get("total_issue_count", 0),
                "tooltip": (
                    f"{DORA_METRICS_TOOLTIPS.get('mean_time_to_recovery', '')} "
                    f"Average calculated over last {n_weeks_display} weeks."
                ),
                "weekly_labels": cached_metrics.get("mean_time_to_recovery", {}).get(
                    "weekly_labels", []
                ),
                "weekly_values": mttr_weekly_values,
                "weekly_values_adjusted": mttr_weekly_values_adjusted,
                "blend_metadata": mttr_blend_metadata,
            },
        }

        logger.info(
            f"DORA: Calculating dynamic forecasts for {data_points} weeks of data"
        )

        metric_type_mapping = {
            "deployment_frequency": "higher_better",
            "lead_time_for_changes": "lower_better",
            "change_failure_rate": "lower_better",
            "mean_time_to_recovery": "lower_better",
        }

        for metric_name in metrics_data.keys():
            weekly_values = metrics_data[metric_name].get(
                "weekly_values_adjusted"
            ) or metrics_data[metric_name].get("weekly_values", [])
            current_value = metrics_data[metric_name].get("value")
            metric_type = metric_type_mapping.get(metric_name, "higher_better")

            forecast_data, trend_vs_forecast = calculate_dynamic_forecast(
                weekly_values=weekly_values,
                current_value=current_value,
                metric_type=metric_type,
                metric_name=metric_name,
            )

            if forecast_data:
                metrics_data[metric_name]["forecast_data"] = forecast_data
                forecast_value = forecast_data.get("forecast_value")
                logger.info(f"Calculated forecast for {metric_name}: {forecast_value}")
            if trend_vs_forecast:
                metrics_data[metric_name]["trend_vs_forecast"] = trend_vs_forecast

        return create_metric_cards_grid(metrics_data), metrics_data

    except PreventUpdate:
        raise
    except Exception as e:
        logger.error(f"Error loading DORA metrics from cache: {e}", exc_info=True)
        return (
            create_metric_cards_grid(
                {
                    "deployment_frequency": {
                        "metric_name": "deployment_frequency",
                        "value": None,
                        "error_state": "error",
                        "error_message": "Error loading metrics - check logs",
                    },
                    "lead_time_for_changes": {
                        "metric_name": "lead_time_for_changes",
                        "value": None,
                        "error_state": "error",
                    },
                    "change_failure_rate": {
                        "metric_name": "change_failure_rate",
                        "value": None,
                        "error_state": "error",
                    },
                    "mean_time_to_recovery": {
                        "metric_name": "mean_time_to_recovery",
                        "value": None,
                        "error_state": "error",
                    },
                }
            ),
            {},
        )
