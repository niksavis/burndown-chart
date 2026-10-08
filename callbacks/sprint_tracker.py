import logging
import traceback

import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, callback_context, html, no_update

from data.persistence.factory import get_backend
from data.sprint_manager import (
    calculate_sprint_progress,
    calculate_sprint_scope_change_points,
    calculate_sprint_scope_changes,
    get_sprint_dates,
    get_sprint_scope_change_issues,
    reconcile_active_sprint_membership,
    select_preferred_sprint,
    sort_sprint_ids_by_recency,
)
from data.sprint_snapshot_calculator import calculate_daily_sprint_snapshots
from data.sprint_tracker_data import load_sprint_tracker_dataset
from ui.empty_states import create_no_sprints_state
from ui.sprint_tracker import (
    create_combined_sprint_controls,
    create_sprint_charts_section,
    create_sprint_scope_changes_view,
    create_sprint_summary_cards,
)
from visualization.sprint_burnup_chart import create_sprint_burnup_chart
from visualization.sprint_charts import (
    create_sprint_progress_bars,
    create_sprint_summary_card,
)

logger = logging.getLogger(__name__)


def _render_sprint_tracker_content(
    data_points_count: int, show_points: bool = False
) -> html.Div:

    logger.info(
        f"Rendering Sprint Tracker content with data_points: {data_points_count}"
    )

    try:
        backend = get_backend()
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            logger.warning("No active profile/query configured")
            return create_no_sprints_state()

        dataset = load_sprint_tracker_dataset(active_profile_id, active_query_id)

        settings = dataset["settings"]
        tracked_issues = dataset["tracked_issues"]
        all_issue_states = dataset["all_issue_states"]
        sprint_field = dataset["sprint_field"]
        sprint_snapshots = dataset["sprint_snapshots"]
        sprint_metadata = dataset["sprint_metadata"]

        if not tracked_issues:
            logger.warning("No tracked issue types (Story/Task/Bug) found")
            return create_no_sprints_state()

        if not sprint_field:
            logger.warning("Sprint field not configured in field mappings")
            return create_no_sprints_state()

        if not sprint_snapshots:
            logger.info("No sprint changelog data found - sprints not configured")
            return create_no_sprints_state()

        selected_sprint = select_preferred_sprint(sprint_snapshots, sprint_metadata)
        if not selected_sprint:
            logger.warning("No sprint snapshots available")
            return create_no_sprints_state()

        selected_sprint_id = selected_sprint["name"]
        sprint_start_date = selected_sprint.get("start_date")
        sprint_end_date = selected_sprint.get("end_date")

        sprint_data = sprint_snapshots[selected_sprint_id]

        logger.info(f"Selected sprint: {selected_sprint_id}")

        flow_start_statuses = settings.get("flow_start_statuses", [])
        flow_wip_statuses = settings.get("wip_statuses", [])
        flow_end_statuses = settings.get("flow_end_statuses", [])
        if not flow_start_statuses:
            flow_start_statuses = ["To Do", "Backlog", "Open"]
        if not flow_wip_statuses:
            flow_wip_statuses = ["In Progress", "In Review", "Testing"]
        if not flow_end_statuses:
            flow_end_statuses = ["Done", "Closed", "Resolved"]

        selected_sprint_state = sprint_metadata.get(selected_sprint_id, {}).get("state")

        if selected_sprint_state == "ACTIVE":
            sprint_data = reconcile_active_sprint_membership(
                sprint_data,
                tracked_issues,
                selected_sprint_id,
                sprint_field,
            )

        scope_window_start = (
            None if selected_sprint_state == "FUTURE" else sprint_start_date
        )

        progress_data = calculate_sprint_progress(
            sprint_data, flow_end_statuses, flow_wip_statuses
        )

        scope_changes = calculate_sprint_scope_changes(sprint_data, scope_window_start)
        scope_change_points = calculate_sprint_scope_change_points(
            sprint_data,
            tracked_issues,
            sprint_start_date=scope_window_start,
            sprint_end_date=sprint_end_date,
        )
        scope_change_issues = get_sprint_scope_change_issues(
            sprint_data,
            sprint_start_date=scope_window_start,
            sprint_end_date=sprint_end_date,
        )

        sprint_changes = {
            "added": sprint_data.get("added_issues", []),
            "removed": sprint_data.get("removed_issues", []),
        }

        summary_card_data = create_sprint_summary_card(
            progress_data, show_points, flow_wip_statuses
        )

        summary_cards = create_sprint_summary_cards(
            selected_sprint_id,
            summary_card_data,
            show_points,
            scope_change_summary={
                "added_after_start": scope_changes.get("added", 0),
                "removed_after_start": scope_changes.get("removed", 0),
                "added_points_after_start": scope_change_points.get(
                    "added_points", 0.0
                ),
                "removed_points_after_start": scope_change_points.get(
                    "removed_points", 0.0
                ),
            },
            sprint_state=selected_sprint_state,
        )
        scope_changes_view = create_sprint_scope_changes_view(
            scope_change_issues,
            sprint_state=selected_sprint_state,
            issue_states=all_issue_states,
        )

        status_changelog = dataset["status_changelog"]

        logger.info(
            "[SPRINT TRACKER] Loaded "
            f"{len(status_changelog)} status changelog entries for sprint"
        )

        progress_bars = create_sprint_progress_bars(
            sprint_data,
            status_changelog,
            show_points,
            sprint_start_date=sprint_start_date,
            sprint_end_date=sprint_end_date,
            flow_start_statuses=flow_start_statuses,
            flow_wip_statuses=flow_wip_statuses,
            flow_end_statuses=flow_end_statuses,
            sprint_changes=sprint_changes,
            sprint_state=selected_sprint_state,
            scope_changes=scope_changes,
        )

        sprint_ids = sort_sprint_ids_by_recency(sprint_snapshots, sprint_metadata)
        combined_controls = (
            create_combined_sprint_controls(
                sprint_ids, selected_sprint_id, sprint_metadata
            )
            if len(sprint_ids) > 1
            else html.Div()
        )

        return html.Div(
            [
                dbc.Container(
                    [
                        html.Div(
                            [
                                combined_controls,
                            ],
                            id="sprint-controls-container",
                        ),
                        create_sprint_charts_section(),
                        html.Div(
                            [
                                summary_cards,
                                scope_changes_view,
                                html.H5("Issue Progress", className="mt-4 mb-3"),
                                progress_bars,
                            ],
                            id="sprint-data-container",
                        ),
                    ],
                    fluid=True,
                    className="mt-4",
                )
            ]
        )

    except Exception as e:
        logger.error(f"Error rendering Sprint Tracker content: {e}")
        logger.error(traceback.format_exc())

        return html.Div(
            [
                dbc.Alert(
                    [
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        html.Strong("Error: "),
                        f"Failed to load Sprint Tracker data: {str(e)}",
                    ],
                    color="danger",
                    className="m-4",
                )
            ]
        )


@callback(
    [
        Output("sprint-charts-collapse", "is_open"),
        Output("toggle-charts-text", "children"),
    ],
    Input("toggle-sprint-charts", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_sprint_charts(n_clicks):

    logger.info(f"toggle_sprint_charts called: n_clicks={n_clicks}")
    if n_clicks is None:
        logger.warning("toggle_sprint_charts: n_clicks is None")
        return False, "Show Charts"

    is_open = n_clicks % 2 == 1
    button_text = "Hide Charts" if is_open else "Show Charts"
    logger.info(
        f"toggle_sprint_charts: returning is_open={is_open}, button_text={button_text}"
    )
    return is_open, button_text


@callback(
    Output("sprint-burnup-chart", "figure"),
    Input("sprint-selector-dropdown", "value"),
    Input("sprint-charts-collapse", "is_open"),
    State("points-toggle", "value"),
    prevent_initial_call=True,
)
def update_sprint_charts(selected_sprint, charts_visible, points_toggle_list):

    triggered = callback_context.triggered[0] if callback_context.triggered else None
    trigger_id = triggered["prop_id"].split(".")[0] if triggered else "unknown"
    logger.info(
        "update_sprint_charts TRIGGERED by: "
        f"{trigger_id} (sprint={selected_sprint}, "
        f"points_toggle={points_toggle_list}, visible={charts_visible})"
    )

    if not selected_sprint:
        logger.info("update_sprint_charts: No sprint selected")
        return no_update

    if not charts_visible:
        logger.info("update_sprint_charts: Charts not visible, skipping update")
        return no_update

    try:
        logger.info(
            f"update_sprint_charts: Starting update for sprint: {selected_sprint}"
        )

        show_points = points_toggle_list and "show" in points_toggle_list
        logger.info(
            f"update_sprint_charts: show_points={show_points}, "
            f"points_toggle_list={points_toggle_list}"
        )

        backend = get_backend()
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        logger.info(
            "update_sprint_charts: "
            f"active_profile_id={active_profile_id}, "
            f"active_query_id={active_query_id}"
        )

        if not active_profile_id or not active_query_id:
            logger.warning("No active profile/query for chart update")
            return no_update

        dataset = load_sprint_tracker_dataset(active_profile_id, active_query_id)
        settings = dataset["settings"]
        tracked_issues = dataset["tracked_issues"]
        sprint_field = dataset["sprint_field"]
        sprint_snapshots = dataset["sprint_snapshots"]
        status_changelog = dataset["status_changelog"]

        logger.info(
            "update_sprint_charts: Loaded "
            f"{len(tracked_issues) if tracked_issues else 0} tracked issues"
        )

        if not tracked_issues:
            logger.warning(
                "update_sprint_charts: No tracked issues found after filtering"
            )
            return no_update

        if not sprint_field:
            logger.warning("update_sprint_charts: No sprint_field configured")
            return no_update

        logger.info(
            f"update_sprint_charts: Built {len(sprint_snapshots)} sprint snapshots"
        )

        if selected_sprint not in sprint_snapshots:
            logger.warning(
                f"Selected sprint {selected_sprint} not in snapshots. "
                f"Available: {list(sprint_snapshots.keys())[:5]}"
            )
            return no_update

        sprint_data = sprint_snapshots[selected_sprint]
        logger.info(
            "update_sprint_charts: Sprint data has "
            f"{len(sprint_data.get('current_issues', []))} current issues"
        )

        sprint_dates = get_sprint_dates(selected_sprint, tracked_issues, sprint_field)
        if not sprint_dates:
            logger.warning(f"No dates found for sprint {selected_sprint}")
            return no_update

        sprint_start_date = sprint_dates.get("start_date")
        sprint_end_date = sprint_dates.get("end_date")
        logger.info(
            "update_sprint_charts: Sprint dates: "
            f"{sprint_start_date} to {sprint_end_date}"
        )

        if not sprint_start_date or not sprint_end_date:
            logger.warning(f"Missing start/end dates for sprint {selected_sprint}")
            return no_update

        flow_end_statuses = settings.get("flow_end_statuses", ["Done", "Closed"])
        logger.info(f"update_sprint_charts: flow_end_statuses={flow_end_statuses}")

        daily_snapshots = calculate_daily_sprint_snapshots(
            sprint_data,
            tracked_issues,
            status_changelog,
            sprint_start_date,
            sprint_end_date,
            flow_end_statuses=flow_end_statuses,
        )

        logger.info(
            "update_sprint_charts: Generated "
            f"{len(daily_snapshots) if daily_snapshots else 0} daily snapshots"
        )

        if daily_snapshots:
            logger.info(f"update_sprint_charts: First snapshot: {daily_snapshots[0]}")
            logger.info(f"update_sprint_charts: Last snapshot: {daily_snapshots[-1]}")
            completed_values = [s.get("completed_points", 0) for s in daily_snapshots]
            scope_values = [s.get("total_scope", 0) for s in daily_snapshots]
            logger.info(
                f"update_sprint_charts: Completed points over time: {completed_values}"
            )
            logger.info(f"update_sprint_charts: Total scope over time: {scope_values}")

        if not daily_snapshots:
            logger.warning(f"No daily snapshots generated for {selected_sprint}")
            return no_update

        burnup_fig = create_sprint_burnup_chart(
            daily_snapshots,
            sprint_name=selected_sprint,
            sprint_start_date=sprint_start_date,
            sprint_end_date=sprint_end_date,
            height=450,
            show_points=show_points,
        )

        logger.info(
            f"Updated sprint chart for {selected_sprint} (show_points={show_points})"
        )
        return burnup_fig

    except Exception as e:
        logger.error(f"Error updating sprint charts: {e}")
        logger.error(traceback.format_exc())
        return no_update
