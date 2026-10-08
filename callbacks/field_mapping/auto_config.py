import logging
from pathlib import Path

import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, html, no_update

from data.auto_configure import generate_smart_defaults
from data.jira import fetch_jira_issues
from data.persistence.factory import get_backend
from data.profile_manager import get_active_profile, get_profile_file_path
from ui.toast_notifications import create_error_toast, create_success_toast

logger = logging.getLogger(__name__)


@callback(
    [
        Output("field-mapping-state-store", "data", allow_duplicate=True),
        Output("field-mapping-status", "children", allow_duplicate=True),
        Output("auto-configure-warning-banner", "is_open", allow_duplicate=True),
        Output("auto-configure-refresh-trigger", "data"),
        Output("auto-configure-confirm-button", "disabled"),
        Output("auto-configure-confirm-button", "children"),
        Output("app-notifications", "children", allow_duplicate=True),
    ],
    Input("auto-configure-confirm-button", "n_clicks"),
    [
        State("jira-metadata-store", "data"),
        State("field-mapping-state-store", "data"),
        State("auto-configure-refresh-trigger", "data"),
    ],
    prevent_initial_call=True,
    running=[
        (Output("auto-configure-confirm-button", "disabled"), True, False),
        (
            Output("auto-configure-confirm-button", "children"),
            [dbc.Spinner(size="sm", spinner_class_name="me-2"), "Configuring..."],
            [html.I(className="fas fa-check me-2"), "Yes, Auto-Configure Now"],
        ),
    ],
)
def auto_configure_from_metadata(
    n_clicks: int, metadata: dict, current_state: dict, current_trigger: int
):

    import json  # noqa: PLC0415

    if not n_clicks:
        return (
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
        )

    try:
        if not metadata or metadata.get("error"):
            return (
                no_update,
                "",
                False,
                no_update,
                False,
                [html.I(className="fas fa-check me-2"), "Yes, Auto-Configure Now"],
                create_error_toast(
                    "JIRA metadata not available. Please ensure JIRA is connected.",
                    header="Cannot Auto-Configure",
                ),
            )

        active_profile = get_active_profile()
        if not active_profile:
            return (
                no_update,
                "",
                False,
                no_update,
                False,
                [html.I(className="fas fa-check me-2"), "Yes, Auto-Configure Now"],
                create_error_toast(
                    "No active profile found.",
                    header="Cannot Auto-Configure",
                ),
            )

        profile_id = active_profile.id
        profile_path = get_profile_file_path(profile_id)

        jql_query = None
        try:
            with open(profile_path, encoding="utf-8") as f:
                profile_data = json.load(f)

                active_query_id = profile_data.get("active_query_id")

                if not active_query_id:
                    queries = profile_data.get("queries", [])
                    if queries and len(queries) > 0:
                        active_query_id = (
                            queries[0].get("id")
                            if isinstance(queries[0], dict)
                            else queries[0]
                        )
                        logger.info(
                            "[AutoConfigure] No active query, "
                            f"using first query: {active_query_id}"
                        )
                    else:
                        queries_dir = Path(profile_path).parent / "queries"
                        if queries_dir.exists():
                            query_dirs = [
                                d for d in queries_dir.iterdir() if d.is_dir()
                            ]
                            if query_dirs:
                                active_query_id = query_dirs[0].name
                                logger.info(
                                    "[AutoConfigure] Found query directory: "
                                    f"{active_query_id}"
                                )

                if active_query_id:
                    backend = get_backend()

                    try:
                        query_data = backend.get_query(profile_id, active_query_id)
                        if query_data:
                            jql_query = query_data.get("jql", "")
                            logger.info(
                                "[AutoConfigure] Loaded JQL query from active query: "
                                f"{jql_query}"
                            )
                        else:
                            logger.warning(
                                f"[AutoConfigure] Query {active_query_id} "
                                "not found in database"
                            )
                    except Exception as qe:
                        logger.warning(f"Could not load query from database: {qe}")
                else:
                    logger.warning(
                        "No active query ID found in profile "
                        "and no fallback queries available"
                    )
        except Exception as e:
            logger.warning(f"Could not load profile data: {e}")

        logger.info(
            f"[AutoConfigure] Generating smart defaults for profile {profile_id}"
        )

        issues = []
        if jql_query:
            try:
                logger.info(
                    "[AutoConfigure] Fetching last 100 issues for field analysis..."
                )
                sample_jql = f"{jql_query} ORDER BY created DESC"

                with open(profile_path, encoding="utf-8") as f:
                    profile_data = json.load(f)
                    jira_config = profile_data.get("jira_config", {})

                fetch_config = {
                    "jql_query": sample_jql,
                    "api_endpoint": jira_config.get("base_url", "").rstrip("/")
                    + "/rest/api/2/search",
                    "token": jira_config.get("token", ""),
                    "story_points_field": jira_config.get("points_field", ""),
                    "field_mappings": {},
                    "fields": "*all",
                }

                success, fetched_issues = fetch_jira_issues(
                    config=fetch_config, max_results=100
                )

                if success:
                    issues = fetched_issues
                    logger.info(
                        f"[AutoConfigure] Fetched {len(issues)} issues for analysis"
                    )
                else:
                    logger.warning(
                        "[AutoConfigure] Failed to fetch issues for field detection"
                    )

            except Exception as e:
                logger.warning(
                    f"[AutoConfigure] Could not fetch issues for field detection: {e}",
                    exc_info=True,
                )

        defaults = generate_smart_defaults(metadata, jql_query, issues)

        new_state = current_state.copy() if current_state else {}

        new_state["flow_end_statuses"] = defaults["project_classification"][
            "flow_end_statuses"
        ]
        new_state["active_statuses"] = defaults["project_classification"][
            "active_statuses"
        ]
        new_state["flow_start_statuses"] = defaults["project_classification"][
            "flow_start_statuses"
        ]
        new_state["wip_statuses"] = defaults["project_classification"]["wip_statuses"]
        new_state["development_projects"] = defaults["project_classification"][
            "development_projects"
        ]
        new_state["devops_projects"] = defaults["project_classification"].get(
            "devops_projects", []
        )

        new_state["flow_feature_issue_types"] = defaults["flow_type_mappings"][
            "Feature"
        ]
        new_state["flow_defect_issue_types"] = defaults["flow_type_mappings"]["Defect"]
        new_state["flow_technical_debt_issue_types"] = defaults[
            "flow_type_mappings"
        ].get("Technical Debt", [])
        new_state["flow_risk_issue_types"] = defaults["flow_type_mappings"].get(
            "Risk", []
        )

        if (
            "project_classification" in defaults
            and "bug_types" in defaults["project_classification"]
        ):
            new_state["bug_types"] = defaults["project_classification"]["bug_types"]
            logger.info(
                "[AutoConfigure] Stored "
                f"{len(new_state['bug_types'])} incident types for UI"
            )

        if (
            "project_classification" in defaults
            and "devops_task_types" in defaults["project_classification"]
        ):
            new_state["devops_task_types"] = defaults["project_classification"][
                "devops_task_types"
            ]
            logger.info(
                "[AutoConfigure] Stored "
                f"{len(new_state['devops_task_types'])} DevOps task types for UI"
            )

        if "field_mappings" in defaults:
            new_state["field_mappings"] = defaults["field_mappings"]

        if "points_field" in defaults:
            if "field_mappings" not in new_state:
                new_state["field_mappings"] = {}
            if "general" not in new_state["field_mappings"]:
                new_state["field_mappings"]["general"] = {}
            new_state["field_mappings"]["general"]["estimate"] = defaults[
                "points_field"
            ]

        if "field_values" in defaults:
            new_state["field_values"] = defaults["field_values"]

        if "project_classification" not in new_state:
            new_state["project_classification"] = {}
        new_state["project_classification"].update(defaults["project_classification"])

        auto_detected_prod = (
            metadata.get("auto_detected", {}).get("production_identifiers", [])
            if metadata
            else []
        )
        if auto_detected_prod:
            new_state["project_classification"]["production_environment_values"] = (
                auto_detected_prod
            )
            new_state["production_environment_values"] = auto_detected_prod
            logger.info(
                "[AutoConfigure] Pre-selected "
                f"{len(auto_detected_prod)} auto-detected production identifiers: "
                f"{auto_detected_prod}"
            )
        elif (
            "field_values" in defaults
            and "target_environment" in defaults["field_values"]
        ):
            logger.info(
                f"[AutoConfigure] No auto-detected production identifiers found. "
                "Available environment values: "
                f"{len(defaults['field_values']['target_environment'])}"
            )

        if "flow_type_mappings" not in new_state:
            new_state["flow_type_mappings"] = {}
        for flow_type, issue_types in defaults["flow_type_mappings"].items():
            if flow_type not in new_state["flow_type_mappings"]:
                new_state["flow_type_mappings"][flow_type] = {
                    "issue_types": [],
                    "effort_categories": [],
                }
            new_state["flow_type_mappings"][flow_type]["issue_types"] = issue_types

            if (
                "field_values" in defaults
                and "effort_category" in defaults["field_values"]
            ):
                new_state["flow_type_mappings"][flow_type]["effort_categories"] = (
                    defaults["field_values"]["effort_category"]
                )
                logger.info(
                    "[AutoConfigure] Populated "
                    f"{len(defaults['field_values']['effort_category'])} "
                    f"effort categories for {flow_type}"
                )

        completion_count = len(defaults["project_classification"]["flow_end_statuses"])
        active_count = len(defaults["project_classification"]["active_statuses"])
        wip_count = len(defaults["project_classification"]["wip_statuses"])
        feature_count = len(defaults["flow_type_mappings"]["Feature"])
        defect_count = len(defaults["flow_type_mappings"]["Defect"])
        project_count = len(defaults["project_classification"]["development_projects"])

        logger.info(
            f"[AutoConfigure] Generated defaults: {completion_count} completion, "
            f"{active_count} active, {wip_count} WIP statuses, "
            f"{feature_count} features, {defect_count} defects, "
            f"{project_count} projects"
        )

        total_statuses = completion_count + active_count + wip_count
        total_types = feature_count + defect_count
        toast = create_success_toast(
            f"{total_statuses} statuses, {total_types} work types, "
            f"{project_count} project{'s' if project_count != 1 else ''}. "
            "Click 'Save Mappings' to apply.",
            header="Auto-Configuration Complete",
            duration=5000,
        )

        new_trigger = (current_trigger or 0) + 1
        return (
            new_state,
            "",
            False,
            new_trigger,
            False,
            [html.I(className="fas fa-check me-2"), "Yes, Auto-Configure Now"],
            toast,
        )

    except Exception as e:
        logger.error(
            f"[AutoConfigure] Error during auto-configuration: {e}", exc_info=True
        )
        return (
            no_update,
            "",
            False,
            no_update,
            False,
            [html.I(className="fas fa-check me-2"), "Yes, Auto-Configure Now"],
            create_error_toast(f"Error: {str(e)}", header="Auto-Configuration Failed"),
        )
