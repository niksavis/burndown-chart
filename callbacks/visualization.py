import json
import logging
from datetime import datetime

import pandas as pd
from dash import (
    Input,
    Output,
    State,
    callback,
    callback_context,
    html,
)
from dash.exceptions import PreventUpdate

from callbacks.active_work_timeline import _render_active_work_timeline_content
from callbacks.bug_analysis import _render_bug_analysis_content
from callbacks.sprint_tracker import _render_sprint_tracker_content
from callbacks.visualization_helpers import check_has_points_in_period
from callbacks.visualization_helpers.burndown_tab import _render_burndown_tab
from callbacks.visualization_helpers.dashboard_tab import _render_dashboard_tab
from callbacks.visualization_helpers.data_checks import filter_df_by_week_labels
from callbacks.visualization_helpers.tab_content import (
    create_scope_tracking_tab_content,
)
from data import compute_cumulative_values
from data.metrics_snapshots import load_snapshots
from data.persistence import load_unified_project_data
from ui.cards.data_cards import create_statistics_data_card
from ui.dora_metrics_dashboard import create_dora_dashboard
from ui.flow_metrics_dashboard import create_flow_dashboard
from ui.loading_utils import create_content_placeholder
from visualization import create_forecast_plot
from visualization.charts import apply_mobile_optimization

logger = logging.getLogger("burndown_chart")


def register(app):

    app.clientside_callback(
        """
        function(n_intervals, init_complete) {
            const width = window.innerWidth;
            if (width < 768) {
                return "mobile";
            } else if (width < 1024) {
                return "tablet";
            } else {
                return "desktop";
            }
        }
        """,
        Output("viewport-size", "data"),
        [Input("viewport-detector", "n_intervals"), Input("app-init-complete", "data")],
    )

    @app.callback(
        Output("app-init-complete", "data"), [Input("chart-tabs", "active_tab")]
    )
    def mark_initialization_complete(active_tab):
        return True

    @app.callback(
        Output("forecast-graph", "figure"),
        [
            Input("current-settings", "modified_timestamp"),
            Input("current-statistics", "modified_timestamp"),
            Input("calculation-results", "data"),
            Input("chart-tabs", "active_tab"),
        ],
        [
            State("current-settings", "data"),
            State("current-statistics", "data"),
            State("viewport-size", "data"),
        ],
    )
    def update_forecast_graph(
        settings_ts,
        statistics_ts,
        calc_results,
        active_tab,
        settings,
        statistics,
        viewport_size,
    ):
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate

        if active_tab != "tab-burndown":
            raise PreventUpdate

        if settings is None or statistics is None:
            raise PreventUpdate

        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if trigger_id == "calculation-results" and calc_results is None:
            raise PreventUpdate

        viewport_size = viewport_size or "desktop"
        is_mobile = viewport_size == "mobile"
        is_tablet = viewport_size == "tablet"

        df = pd.DataFrame(statistics)
        if len(df) > 0:
            df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")
            df = df.sort_values("date")

        total_items = settings.get("total_items", 100)
        total_points = settings.get("total_points", 500)
        pert_factor = settings.get("pert_factor", 3)
        deadline = settings.get("deadline", None)
        data_points_count = int(settings.get("data_points_count", len(df)))

        show_milestone = settings.get("show_milestone", False)
        milestone = settings.get("milestone", None) if show_milestone else None

        if not df.empty:
            df = compute_cumulative_values(df, total_items, total_points)

        fig, _ = create_forecast_plot(
            df=df,
            total_items=total_items,
            total_points=total_points,
            pert_factor=pert_factor,
            deadline_str=deadline,
            milestone_str=milestone,
            data_points_count=data_points_count,
            show_points=settings.get("show_points", False),
        )

        fig, _ = apply_mobile_optimization(
            fig,
            is_mobile=is_mobile,
            is_tablet=is_tablet,
            title="Burndown Forecast" if not is_mobile else None,
        )

        return fig

    @app.callback(
        [
            Output("tab-content", "children"),
            Output("chart-cache", "data"),
            Output("ui-state", "data"),
        ],
        [
            Input("chart-tabs", "active_tab"),
            Input("current-settings", "modified_timestamp"),
            Input("current-statistics", "modified_timestamp"),
            Input("calculation-results", "data"),
            Input("date-range-weeks", "data"),
            Input("points-toggle", "value"),
            Input("budget-settings-store", "data"),
            Input("metrics-refresh-trigger", "data"),
        ],
        [
            State("current-settings", "data"),
            State("current-statistics", "data"),
            State("chart-cache", "data"),
            State("ui-state", "data"),
            State("viewport-size", "data"),
        ],
    )
    def render_tab_content(
        active_tab,
        settings_ts,
        statistics_ts,
        calc_results,
        date_range_weeks,
        show_points,
        budget_store,
        import_trigger,
        settings,
        statistics,
        chart_cache,
        ui_state,
        viewport_size,
    ):

        ctx = callback_context
        trigger_info = ctx.triggered[0]["prop_id"] if ctx.triggered else "initial"
        logger.debug(
            "[CTO DEBUG] render_tab_content triggered by: "
            f"{trigger_info}, active_tab='{active_tab}', "
            f"cache_size={len(chart_cache) if chart_cache else 0}"
        )

        if statistics:
            logger.info(
                "[VISUALIZATION] render_tab_content received "
                f"{len(statistics)} statistics"
            )
            logger.info(
                "[VISUALIZATION] First stat: "
                f"date={statistics[0].get('date')}, "
                f"items={statistics[0].get('remaining_items')}, "
                f"points={statistics[0].get('remaining_total_points')}"
            )
            logger.info(
                "[VISUALIZATION] Last stat: "
                f"date={statistics[-1].get('date')}, "
                f"items={statistics[-1].get('remaining_items')}, "
                f"points={statistics[-1].get('remaining_total_points')}"
            )
        else:
            logger.warning(
                "[VISUALIZATION] render_tab_content received EMPTY statistics!"
            )

        if not active_tab:
            logger.debug(
                "[CTO DEBUG] active_tab was empty/None, defaulting to tab-burndown"
            )
            active_tab = "tab-burndown"

        if not settings or not statistics:
            ui_state = ui_state or {"loading": False, "last_tab": None}
            chart_cache = chart_cache or {}
            error_content = create_content_placeholder(
                type="chart",
                text="No data available. Please load project data first.",
                height="400px",
            )
            return error_content, chart_cache, ui_state

        if chart_cache is None:
            chart_cache = {}
        if ui_state is None:
            ui_state = {"loading": False, "last_tab": None}

        viewport_size = viewport_size or "desktop"
        is_mobile = viewport_size == "mobile"
        is_tablet = viewport_size == "tablet"
        logger.info(
            f"Rendering charts for viewport: {viewport_size} "
            f"(mobile={is_mobile}, tablet={is_tablet})"
        )

        show_points = bool(
            show_points and (show_points is True or "show" in show_points)
        )

        trigger_info = ctx.triggered[0]["prop_id"] if ctx.triggered else ""
        if "chart-tabs" in trigger_info:
            logger.debug(
                "[CTO DEBUG] Tab switch detected - "
                "CLEARING ALL CACHE to prevent contamination"
            )
            chart_cache = {}
        elif "budget-settings-store" in trigger_info:
            logger.debug(
                "[CTO DEBUG] Budget change detected - "
                "CLEARING ALL CACHE to refresh budget cards"
            )
            chart_cache = {}
        elif "metrics-refresh-trigger" in trigger_info:
            logger.debug(
                "[CTO DEBUG] Import/refresh detected - "
                "CLEARING ALL CACHE to reload data"
            )
            chart_cache = {}
        elif "current-statistics.modified_timestamp" in trigger_info:
            logger.debug(
                "[CTO DEBUG] Statistics modified (table edit) - "
                "CLEARING ALL CACHE to show changes immediately"
            )
            chart_cache = {}
        elif len(chart_cache) > 5:
            oldest_keys = list(chart_cache.keys())[:-5]
            for old_key in oldest_keys:
                if old_key in chart_cache:
                    del chart_cache[old_key]

        data_hash = hash(
            str(statistics)
            + str(settings)
            + str(show_points)
            + str(budget_store)
            + str(import_trigger)
        )
        cache_key = f"{active_tab}_{data_hash}"
        use_cache_for_tab = active_tab != "tab-active-work-timeline"
        logger.debug(f"[CTO DEBUG] Cache key generated: {cache_key}")

        if use_cache_for_tab and cache_key in chart_cache:
            logger.debug(
                "[CTO DEBUG] Returning CACHED content for "
                f"active_tab='{active_tab}', cache_key={cache_key}"
            )
            ui_state["loading"] = False
            ui_state["last_tab"] = active_tab
            return chart_cache[cache_key], chart_cache, ui_state

        ui_state["loading"] = True
        ui_state["last_tab"] = active_tab

        try:
            data_points_count = int(settings.get("data_points_count", 12))

            df = pd.DataFrame(statistics)

            if active_tab == "tab-dashboard":
                logger.debug(
                    "[CTO DEBUG] Creating NEW modern dashboard "
                    f"content, cache_key={cache_key}"
                )
                dashboard_content = _render_dashboard_tab(df, settings, show_points)
                chart_cache[cache_key] = dashboard_content
                ui_state["loading"] = False
                return dashboard_content, chart_cache, ui_state
            elif active_tab == "tab-burndown":
                logger.debug(
                    f"[CTO DEBUG] Creating NEW burndown content, cache_key={cache_key}"
                )
                burndown_tab_content = _render_burndown_tab(
                    df,
                    statistics,
                    settings,
                    show_points,
                    data_points_count,
                    is_mobile,
                    is_tablet,
                )
                chart_cache[cache_key] = burndown_tab_content
                ui_state["loading"] = False
                return burndown_tab_content, chart_cache, ui_state

            elif active_tab == "tab-scope-tracking":
                logger.debug(
                    "[CTO DEBUG] Creating NEW scope tracking content, "
                    f"cache_key={cache_key}"
                )
                df_for_scope = filter_df_by_week_labels(df.copy(), data_points_count)
                has_points_data = show_points and check_has_points_in_period(
                    statistics, data_points_count
                )
                scope_tab_content = create_scope_tracking_tab_content(
                    df_for_scope, settings, show_points and has_points_data
                )
                chart_cache[cache_key] = scope_tab_content
                ui_state["loading"] = False
                return scope_tab_content, chart_cache, ui_state

            elif active_tab == "tab-bug-analysis":
                data_points_count = int(settings.get("data_points_count", 12))

                has_points_data = False
                if show_points:
                    has_points_data = check_has_points_in_period(
                        statistics, data_points_count
                    )

                bug_analysis_content = _render_bug_analysis_content(
                    data_points_count, show_points, has_points_data
                )

                chart_cache[cache_key] = bug_analysis_content
                ui_state["loading"] = False
                return bug_analysis_content, chart_cache, ui_state

            elif active_tab == "tab-dora-metrics":
                dora_content = create_dora_dashboard()

                chart_cache[cache_key] = dora_content
                ui_state["loading"] = False
                return dora_content, chart_cache, ui_state

            elif active_tab == "tab-flow-metrics":
                flow_content = create_flow_dashboard()

                chart_cache[cache_key] = flow_content
                ui_state["loading"] = False
                return flow_content, chart_cache, ui_state

            elif active_tab == "tab-statistics-data":
                statistics_content = create_statistics_data_card(statistics)

                chart_cache[cache_key] = statistics_content
                ui_state["loading"] = False
                return statistics_content, chart_cache, ui_state

            elif active_tab == "tab-sprint-tracker":
                data_points_count = int(settings.get("data_points_count", 12))

                sprint_tracker_content = _render_sprint_tracker_content(
                    data_points_count, show_points
                )

                chart_cache[cache_key] = sprint_tracker_content
                ui_state["loading"] = False
                return sprint_tracker_content, chart_cache, ui_state

            elif active_tab == "tab-active-work-timeline":
                data_points_count = int(settings.get("data_points_count", 12))

                timeline_content = _render_active_work_timeline_content(
                    show_points, data_points_count
                )

                if use_cache_for_tab:
                    chart_cache[cache_key] = timeline_content
                ui_state["loading"] = False
                return timeline_content, chart_cache, ui_state

            fallback_content = create_content_placeholder(
                type="chart", text="Select a tab to view data", height="400px"
            )
            ui_state["loading"] = False
            return fallback_content, chart_cache, ui_state

        except Exception as e:
            import traceback  # noqa: PLC0415

            logger.error(f"Error in render_tab_content callback: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            error_content = html.Div(
                [
                    html.H4("Error Loading Chart", className="text-danger"),
                    html.P(f"An error occurred: {str(e)}"),
                    html.P(
                        "Please check the application logs for details.",
                        className="text-muted",
                    ),
                ]
            )
            ui_state["loading"] = False
            return error_content, chart_cache, ui_state

    @app.callback(
        Output("date-range-weeks", "data"),
        [
            Input({"type": "date-range-slider", "tab": "ALL"}, "value"),
        ],
    )
    def update_date_range(value):
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate

        trigger = ctx.triggered[0]
        value = trigger["value"]

        if value is None:
            return 24

        return value

    @app.callback(
        Output("export-project-data-download", "data"),
        Input("export-project-data-button", "n_clicks"),
        prevent_initial_call=True,
    )
    def export_project_data(n_clicks):

        if not n_clicks:
            raise PreventUpdate

        try:
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

            project_data = load_unified_project_data()

            metrics_snapshots = load_snapshots()

            export_package = {
                "export_timestamp": current_time,
                "project_data": project_data,
                "metrics_snapshots": metrics_snapshots,
                "format_version": "1.0",
            }

            filename = f"project_data_{current_time}.json"

            json_content = json.dumps(export_package, indent=2, ensure_ascii=False)

            logger.info(
                f"Exported project data with {len(metrics_snapshots)} metric snapshots"
            )

            return dict(
                content=json_content, filename=filename, type="application/json"
            )

        except Exception as e:
            logger.error(f"Error exporting project data: {e}")
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            error_data = {"error": f"Failed to export project data: {str(e)}"}
            error_json = json.dumps(error_data, indent=2)
            return dict(
                content=error_json,
                filename=f"export_error_{current_time}.json",
                type="application/json",
            )


def toggle_items_forecast_info_collapse(n_clicks, is_open):
    if n_clicks is None:
        return False

    return not is_open


@callback(
    Output("points-forecast-info-collapse", "is_open"),
    Input("points-forecast-info-collapse-button", "n_clicks"),
    State("points-forecast-info-collapse", "is_open"),
)
def toggle_points_forecast_info_collapse(n_clicks, is_open):
    if n_clicks is None:
        return False

    return not is_open


@callback(
    Output("forecast-info-collapse", "is_open"),
    Input("forecast-info-collapse-button", "n_clicks"),
    State("forecast-info-collapse", "is_open"),
)
def toggle_forecast_info_collapse(n_clicks, is_open):
    if n_clicks is None:
        return False

    return not is_open
