import logging

from dash import Input, Output, State, callback, callback_context, ctx, html, no_update

from data.field_mapper import fetch_available_jira_fields
from data.persistence import load_app_settings
from ui.environment_config_form import create_environment_config_form
from ui.field_mapping_modal import create_field_mapping_form
from ui.issue_type_config_form import create_issue_type_config_form
from ui.project_config_form import create_project_config_form
from ui.status_config_form import create_status_config_form

logger = logging.getLogger(__name__)


@callback(
    Output("field-mapping-content", "children"),
    Output("field-mapping-state-store", "data", allow_duplicate=True),
    Input("mappings-tabs", "active_tab"),
    Input("jira-metadata-store", "data"),
    Input("field-mapping-modal", "is_open"),
    Input("auto-configure-refresh-trigger", "data"),
    Input("fetched-field-values-store", "data"),
    Input("profile-switch-trigger", "data"),
    State("field-mapping-state-store", "data"),
    State("namespace-collected-values", "data"),
    prevent_initial_call="initial_duplicate",
)
def render_tab_content(
    active_tab: str,
    metadata: dict,
    is_open: bool,
    refresh_trigger: int,
    fetched_field_values: dict,
    profile_switch_trigger: int,
    state_data: dict,
    collected_namespace_values: dict,
):

    try:
        triggered_id = ctx.triggered_id if ctx.triggered else None
    except Exception:
        triggered_id = None

    metadata_status = (
        "None"
        if metadata is None
        else (
            f"error: {metadata.get('error')}"
            if metadata.get("error")
            else f"{len(metadata.get('fields', []))} fields"
        )
    )
    logger.info(
        f"[FieldMapping] render_tab_content: tab={active_tab}, is_open={is_open}, "
        f"metadata={metadata_status}, "
        f"collected_values={bool(collected_namespace_values)}, "
        f"fetched_values={list((fetched_field_values or {}).keys())}, "
        f"triggered_by={triggered_id}"
    )

    if triggered_id == "fetched-field-values-store" and active_tab == "tab-fields":
        logger.info(
            "[FieldMapping] Skipping Fields tab re-render on fetched values change"
        )
        return no_update, no_update

    if not is_open and callback_context.triggered:
        return html.Div(), no_update

    settings = load_app_settings()
    metadata = metadata or {}

    state_data = state_data or {}

    if collected_namespace_values and triggered_id != "field-mapping-modal":
        state_data = state_data.copy()
        field_mappings = (
            state_data.get("field_mappings", {}).copy()
            if state_data.get("field_mappings")
            else {}
        )

        actual_values = collected_namespace_values.get("values", {})
        if not actual_values and "_trigger" not in collected_namespace_values:
            actual_values = collected_namespace_values

        collected_keys = (
            list(collected_namespace_values.keys())
            if isinstance(collected_namespace_values, dict)
            else "NOT DICT"
        )

        logger.debug(
            "[FieldMapping] collected_namespace_values type: "
            f"{type(collected_namespace_values)}, "
            "keys: "
            f"{collected_keys}"
        )
        logger.debug(
            f"[FieldMapping] actual_values type: {type(actual_values)}, "
            f"content: {actual_values}"
        )

        for metric, fields in actual_values.items():
            if not isinstance(fields, dict):
                logger.debug(
                    f"[FieldMapping] Skipping non-dict entry: {metric}={fields}"
                )
                continue
            if metric not in field_mappings:
                field_mappings[metric] = {}
            elif not isinstance(field_mappings[metric], dict):
                field_mappings[metric] = {}
            for field, value in fields.items():
                if value:
                    field_mappings[metric][field] = value
                    logger.debug(
                        "[FieldMapping] Merged collected value: "
                        f"{metric}.{field} = {value}"
                    )

        state_data["field_mappings"] = field_mappings
        logger.info(
            "[FieldMapping] Merged "
            f"{len(collected_namespace_values)} metric groups "
            "from collected values"
        )
    elif collected_namespace_values and triggered_id == "field-mapping-modal":
        logger.info(
            "[FieldMapping] Skipping merge of collected_namespace_values - "
            "modal just opened, values are stale from previous save"
        )

    essential_keys = {"_profile_id", "field_mappings"}
    is_partial_state = not state_data or set(state_data.keys()).issubset(essential_keys)

    if is_partial_state:
        existing_field_mappings = state_data.get("field_mappings", {})

        flow_mappings = settings.get("flow_type_mappings", {}) or {}

        def safe_get_flow_mapping(flow_type, key):
            flow_config = flow_mappings.get(flow_type, {})
            if flow_config is None:
                return []
            return flow_config.get(key, []) or []

        profile_id = (state_data or {}).get("_profile_id")

        state_data = {
            "_profile_id": profile_id,
            "field_mappings": settings.get("field_mappings", {}),
            "development_projects": settings.get("development_projects", []),
            "devops_projects": settings.get("devops_projects", []),
            "devops_task_types": settings.get("devops_task_types", []),
            "bug_types": settings.get("bug_types", []),
            "story_types": settings.get("story_types", []),
            "task_types": settings.get("task_types", []),
            "flow_feature_issue_types": safe_get_flow_mapping("Feature", "issue_types"),
            "flow_feature_effort_categories": safe_get_flow_mapping(
                "Feature", "effort_categories"
            ),
            "flow_defect_issue_types": safe_get_flow_mapping("Defect", "issue_types"),
            "flow_defect_effort_categories": safe_get_flow_mapping(
                "Defect", "effort_categories"
            ),
            "flow_technical_debt_issue_types": safe_get_flow_mapping(
                "Technical Debt", "issue_types"
            ),
            "flow_technical_debt_effort_categories": safe_get_flow_mapping(
                "Technical Debt", "effort_categories"
            ),
            "flow_risk_issue_types": safe_get_flow_mapping("Risk", "issue_types"),
            "flow_risk_effort_categories": safe_get_flow_mapping(
                "Risk", "effort_categories"
            ),
            "flow_end_statuses": settings.get("flow_end_statuses", []),
            "active_statuses": settings.get("active_statuses", []),
            "flow_start_statuses": settings.get("flow_start_statuses", []),
            "wip_statuses": settings.get("wip_statuses", []),
            "production_environment_values": settings.get(
                "production_environment_values", []
            ),
        }

        jira_points_field = (
            settings.get("jira_config", {}).get("points_field", "").strip()
        )
        if jira_points_field:
            if "field_mappings" not in state_data:
                state_data["field_mappings"] = {}
            if "general" not in state_data["field_mappings"]:
                state_data["field_mappings"]["general"] = {}
            if not state_data["field_mappings"]["general"].get("estimate"):
                state_data["field_mappings"]["general"]["estimate"] = jira_points_field
                logger.info(
                    "[FieldMapping] Prefilled Estimate from jira_config points_field"
                )

        if existing_field_mappings:
            if "field_mappings" not in state_data:
                state_data["field_mappings"] = {}
            for metric, fields in existing_field_mappings.items():
                if isinstance(fields, dict):
                    if metric not in state_data["field_mappings"]:
                        state_data["field_mappings"][metric] = {}
                    for field, value in fields.items():
                        if value:
                            state_data["field_mappings"][metric][field] = value

        logger.info("[FieldMapping] Initialized state store from saved settings")

    display_settings = state_data.copy()

    if active_tab == "tab-fields":
        try:
            if metadata and metadata.get("error"):
                logger.warning(
                    "[FieldMapping] Metadata has error state: "
                    f"{metadata.get('error')}. "
                    "Fields tab will be empty. Check JIRA configuration."
                )
                current_mappings = {
                    "field_mappings": display_settings.get("field_mappings", {})
                }
                return create_field_mapping_form([], current_mappings), state_data

            cached_fields = metadata.get("fields", []) if metadata else []

            available_fields = []
            for field in cached_fields:
                available_fields.append(
                    {
                        "field_id": field.get("id", ""),
                        "field_name": field.get("name", ""),
                        "field_type": field.get("type", "string"),
                        "is_custom": field.get("custom", False),
                    }
                )

            if not available_fields:
                logger.warning(
                    "[FieldMapping] No cached fields found, fetching from JIRA..."
                )
                available_fields = fetch_available_jira_fields()

            current_mappings = {
                "field_mappings": display_settings.get("field_mappings", {})
            }

            general_for_render = current_mappings.get("field_mappings", {}).get(
                "general", {}
            )
            logger.info(
                f"[FieldMapping] Rendering Fields tab with general mappings: "
                f"{len(general_for_render)} fields = {list(general_for_render.keys())}"
            )

            return create_field_mapping_form(
                available_fields, current_mappings
            ), state_data
        except Exception as e:
            logger.error(f"[FieldMapping] Error loading field mappings: {e}")
            return create_field_mapping_form([], {}), state_data

    elif active_tab == "tab-projects":
        return create_project_config_form(
            development_projects=display_settings.get("development_projects", []),
            devops_projects=display_settings.get("devops_projects", []),
            available_projects=metadata.get("projects", []),
        ), state_data

    elif active_tab == "tab-types":
        flow_type_mappings = {
            "Feature": {
                "issue_types": display_settings.get("flow_feature_issue_types", []),
                "effort_categories": display_settings.get(
                    "flow_feature_effort_categories", []
                ),
            },
            "Defect": {
                "issue_types": display_settings.get("flow_defect_issue_types", []),
                "effort_categories": display_settings.get(
                    "flow_defect_effort_categories", []
                ),
            },
            "Technical Debt": {
                "issue_types": display_settings.get(
                    "flow_technical_debt_issue_types", []
                ),
                "effort_categories": display_settings.get(
                    "flow_technical_debt_effort_categories", []
                ),
            },
            "Risk": {
                "issue_types": display_settings.get("flow_risk_issue_types", []),
                "effort_categories": display_settings.get(
                    "flow_risk_effort_categories", []
                ),
            },
        }

        available_effort_categories = []

        if fetched_field_values and fetched_field_values.get("effort_category"):
            available_effort_categories = fetched_field_values["effort_category"].get(
                "values", []
            )
            logger.info(
                "[FieldMapping] Using "
                f"{len(available_effort_categories)} dynamically fetched "
                "effort categories"
            )
        else:
            flow_field_mappings = settings.get("field_mappings", {}).get("flow", {})
            effort_category_field = flow_field_mappings.get("effort_category")
            if effort_category_field and metadata.get("field_options"):
                available_effort_categories = metadata.get("field_options", {}).get(
                    effort_category_field, []
                )
                logger.info(
                    "[FieldMapping] Using "
                    f"{len(available_effort_categories)} effort categories "
                    "from metadata"
                )

        available_issue_types_list = metadata.get("issue_types", [])
        logger.info(
            "[FieldMapping] Rendering Types tab with "
            f"{len(available_issue_types_list)} available issue types"
        )
        feature_count = len(
            flow_type_mappings.get("Feature", {}).get("issue_types", [])
        )
        defect_count = len(flow_type_mappings.get("Defect", {}).get("issue_types", []))
        technical_debt_count = len(
            flow_type_mappings.get("Technical Debt", {}).get("issue_types", [])
        )
        risk_count = len(flow_type_mappings.get("Risk", {}).get("issue_types", []))
        logger.info(
            "[FieldMapping] Flow type mappings: "
            "Feature="
            f"{feature_count}, "
            "Defect="
            f"{defect_count}, "
            "TechnicalDebt="
            f"{technical_debt_count}, "
            f"Risk={risk_count}"
        )

        parent_issue_types = (
            settings.get("field_mappings", {})
            .get("general", {})
            .get("parent_issue_types", [])
        )
        logger.info(
            f"[FieldMapping] Parent issue types configured: {parent_issue_types}"
        )

        return create_issue_type_config_form(
            devops_task_types=display_settings.get("devops_task_types", []),
            bug_types=display_settings.get("bug_types", []),
            story_types=display_settings.get("story_types", []),
            task_types=display_settings.get("task_types", []),
            available_issue_types=available_issue_types_list,
            flow_type_mappings=flow_type_mappings,
            available_effort_categories=available_effort_categories,
            parent_issue_types=parent_issue_types,
        ), state_data

    elif active_tab == "tab-status":
        return create_status_config_form(
            flow_end_statuses=display_settings.get("flow_end_statuses", []),
            active_statuses=display_settings.get("active_statuses", []),
            flow_start_statuses=display_settings.get("flow_start_statuses", []),
            wip_statuses=display_settings.get("wip_statuses", []),
            available_statuses=metadata.get("statuses", []),
        ), state_data

    elif active_tab == "tab-environment":
        dora_mappings = settings.get("field_mappings", {}).get("dora", {})
        affected_env_field = dora_mappings.get("affected_environment")

        available_env_values = []
        metadata_env_values = []
        fetched_env_values = []

        if affected_env_field and metadata.get("field_options"):
            metadata_env_values = metadata.get("field_options", {}).get(
                affected_env_field, []
            )
            logger.debug(
                "[FieldMapping] Loaded "
                f"{len(metadata_env_values)} values from "
                f"metadata.field_options[{affected_env_field}]"
            )

        if fetched_field_values and fetched_field_values.get("affected_environment"):
            fetched_env_values = fetched_field_values["affected_environment"].get(
                "values", []
            )
            logger.debug(
                "[FieldMapping] Loaded "
                f"{len(fetched_env_values)} values from "
                "fetched-field-values-store"
            )

        available_env_values = list(set(metadata_env_values + fetched_env_values))

        if not available_env_values:
            field_values = (state_data or {}).get("field_values", {})
            if field_values and "target_environment" in field_values:
                available_env_values = field_values["target_environment"]
                if len(available_env_values) > 50:
                    logger.warning(
                        "[FieldMapping] Truncating environment values "
                        f"from {len(available_env_values)} to 50"
                    )
                    available_env_values = available_env_values[:50]
                logger.debug(
                    "[FieldMapping] Loaded "
                    f"{len(available_env_values)} values from "
                    "state_data.field_values.target_environment"
                )

        if not available_env_values:
            auto_detected = (metadata or {}).get("auto_detected", {})
            prod_identifiers = auto_detected.get("production_identifiers", [])
            if prod_identifiers:
                available_env_values = prod_identifiers
                logger.debug(
                    "[FieldMapping] Using "
                    f"{len(available_env_values)} auto-detected "
                    "production identifiers as options"
                )

        return create_environment_config_form(
            production_environment_values=display_settings.get(
                "production_environment_values", []
            ),
            available_environment_values=available_env_values,
        ), state_data

    return html.Div("Select a tab to configure mappings."), state_data
