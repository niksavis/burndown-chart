import logging

from dash import ALL, Input, Output, State, callback, ctx, no_update

logger = logging.getLogger(__name__)


@callback(
    Output("field-mapping-state-store", "data"),
    Input({"type": "field-mapping-dropdown", "metric": ALL, "field": ALL}, "value"),
    State("field-mapping-state-store", "data"),
    prevent_initial_call=True,
)
def track_form_state_changes(*args):

    current_state = args[-1] or {}

    triggered = ctx.triggered_id

    if not triggered:
        return no_update

    new_value = ctx.triggered[0]["value"]

    if isinstance(triggered, dict):
        if triggered.get("type") == "field-mapping-dropdown":
            metric = triggered.get("metric")
            field = triggered.get("field")

            if "field_mappings" not in current_state:
                current_state["field_mappings"] = {}
            if metric not in current_state["field_mappings"]:
                current_state["field_mappings"][metric] = {}

            if isinstance(new_value, list):
                if new_value:
                    current_state["field_mappings"][metric][field] = new_value[0]
                elif field in current_state.get("field_mappings", {}).get(metric, {}):
                    del current_state["field_mappings"][metric][field]
            else:
                if new_value:
                    current_state["field_mappings"][metric][field] = new_value
                elif field in current_state.get("field_mappings", {}).get(metric, {}):
                    del current_state["field_mappings"][metric][field]

    logger.info(f"[StateTracking] Updated state for {triggered}: {new_value}")

    return current_state


@callback(
    Output("field-mapping-state-store", "data", allow_duplicate=True),
    Input("development-projects-dropdown", "value"),
    Input("devops-projects-dropdown", "value"),
    State("field-mapping-state-store", "data"),
    prevent_initial_call=True,
)
def track_projects_tab_changes(dev_projects, devops_projects, current_state):
    current_state = current_state or {}
    current_state["development_projects"] = (
        dev_projects
        if isinstance(dev_projects, list)
        else ([dev_projects] if dev_projects else [])
    )
    current_state["devops_projects"] = (
        devops_projects
        if isinstance(devops_projects, list)
        else ([devops_projects] if devops_projects else [])
    )
    return current_state


@callback(
    Output("field-mapping-state-store", "data", allow_duplicate=True),
    Input("devops-task-types-dropdown", "value"),
    Input("bug-types-dropdown", "value"),
    Input("parent-issue-types-dropdown", "value"),
    Input("flow-feature-issue-types-dropdown", "value"),
    Input("flow-feature-effort-categories-dropdown", "value"),
    Input("flow-defect-issue-types-dropdown", "value"),
    Input("flow-defect-effort-categories-dropdown", "value"),
    Input("flow-technical-debt-issue-types-dropdown", "value"),
    Input("flow-technical-debt-effort-categories-dropdown", "value"),
    Input("flow-risk-issue-types-dropdown", "value"),
    Input("flow-risk-effort-categories-dropdown", "value"),
    State("field-mapping-state-store", "data"),
    prevent_initial_call=True,
)
def track_types_tab_changes(*args):
    current_state = args[-1] or {}

    state_keys = [
        "devops_task_types",
        "bug_types",
        "parent_issue_types",
        "flow_feature_issue_types",
        "flow_feature_effort_categories",
        "flow_defect_issue_types",
        "flow_defect_effort_categories",
        "flow_technical_debt_issue_types",
        "flow_technical_debt_effort_categories",
        "flow_risk_issue_types",
        "flow_risk_effort_categories",
    ]

    for i, key in enumerate(state_keys):
        value = args[i]
        current_state[key] = (
            value if isinstance(value, list) else ([value] if value else [])
        )
        if key in ("parent_issue_types", "flow_technical_debt_issue_types") and value:
            logger.info(
                f"[FieldMapping] track_types_tab_changes: Storing {key}={value}"
            )

    return current_state


@callback(
    Output("field-mapping-state-store", "data", allow_duplicate=True),
    Input("completion-statuses-dropdown", "value"),
    Input("active-statuses-dropdown", "value"),
    Input("flow-start-statuses-dropdown", "value"),
    Input("wip-statuses-dropdown", "value"),
    State("field-mapping-state-store", "data"),
    prevent_initial_call=True,
)
def track_status_tab_changes(completion, active, flow_start, wip, current_state):
    current_state = current_state or {}
    current_state["flow_end_statuses"] = (
        completion
        if isinstance(completion, list)
        else ([completion] if completion else [])
    )
    current_state["active_statuses"] = (
        active if isinstance(active, list) else ([active] if active else [])
    )
    current_state["flow_start_statuses"] = (
        flow_start
        if isinstance(flow_start, list)
        else ([flow_start] if flow_start else [])
    )
    current_state["wip_statuses"] = (
        wip if isinstance(wip, list) else ([wip] if wip else [])
    )
    return current_state


@callback(
    Output("field-mapping-state-store", "data", allow_duplicate=True),
    Input("production-environment-values-dropdown", "value"),
    State("field-mapping-state-store", "data"),
    prevent_initial_call=True,
)
def track_environment_tab_changes(prod_env, current_state):

    if not ctx.triggered or not ctx.triggered[0]["value"]:
        return no_update

    current_state = current_state or {}
    current_state["production_environment_values"] = (
        prod_env if isinstance(prod_env, list) else ([prod_env] if prod_env else [])
    )
    return current_state
