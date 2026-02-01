"""Tab content rendering for field mapping modal.

Handles rendering of all tabs (Fields, Projects, Types, Status, Environment)
with state persistence and metadata integration.
"""

import logging
from dash import callback, Output, Input, State, html, no_update, callback_context
from ui.field_mapping_modal import create_field_mapping_form
from data.field_mapper import fetch_available_jira_fields

logger = logging.getLogger(__name__)


@callback(
    Output("field-mapping-content", "children"),
    Output("field-mapping-state-store", "data", allow_duplicate=True),
    Input("mappings-tabs", "active_tab"),
    Input("jira-metadata-store", "data"),
    Input("field-mapping-modal", "is_open"),
    Input("auto-configure-refresh-trigger", "data"),  # Trigger from auto-configure
    Input(
        "fetched-field-values-store", "data"
    ),  # Trigger re-render when field values fetched (for Types/Environment tabs)
    Input(
        "profile-switch-trigger", "data"
    ),  # NEW: Refresh when profile switches (import)
    State("field-mapping-state-store", "data"),  # Read-only state access
    State("namespace-collected-values", "data"),  # Collected namespace values from DOM
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
    """Render appropriate form based on active tab.

    This callback now uses the state store for all form values, ensuring
    data is preserved across tab switches.

    Args:
        active_tab: ID of currently active tab
        metadata: Cached JIRA metadata from store
        is_open: Whether modal is open
        refresh_trigger: Trigger value from auto-configure
        fetched_field_values: Dynamically fetched field values (triggers re-render for Types/Env tabs)
        profile_switch_trigger: Trigger value from profile switch (import)
        state_data: Current form state from state store
        collected_namespace_values: Values collected from namespace inputs (DOM)

    Returns:
        Tuple of (form component, updated state)
    """
    from dash import ctx
    from data.persistence import load_app_settings
    from ui.project_config_form import create_project_config_form
    from ui.issue_type_config_form import create_issue_type_config_form
    from ui.status_config_form import create_status_config_form
    from ui.environment_config_form import create_environment_config_form

    # Check what triggered this callback
    triggered_id = ctx.triggered_id if ctx.triggered else None

    # Debug logging
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

    # If triggered by fetched-field-values-store and we're on Fields tab, don't re-render
    # This prevents losing namespace input values when field values are fetched
    if triggered_id == "fetched-field-values-store" and active_tab == "tab-fields":
        logger.info(
            "[FieldMapping] Skipping Fields tab re-render on fetched values change"
        )
        return no_update, no_update

    # Don't render if modal is closed (but allow initial empty state)
    if not is_open and callback_context.triggered:
        return html.Div(), no_update

    # Initialize state from saved settings on first open
    settings = load_app_settings()
    metadata = metadata or {}

    # Ensure state_data is a dict
    state_data = state_data or {}

    # Merge collected namespace values into state_data field_mappings
    # This preserves values when switching tabs
    # IMPORTANT: Do this BEFORE checking for empty state
    # CRITICAL: Only merge if triggered by tab switch, NOT when modal opens
    # When modal opens, collected_namespace_values contains STALE data from previous save
    # which causes cleared fields to reappear (Bug: general fields reappearing after clear+save)
    if collected_namespace_values and triggered_id != "field-mapping-modal":
        state_data = state_data.copy()  # Don't mutate original
        field_mappings = (
            state_data.get("field_mappings", {}).copy()
            if state_data.get("field_mappings")
            else {}
        )

        # collected_namespace_values format: {_trigger: "save"|"mode_switch", values: {metric: {field: value}}}
        # Extract actual values from the wrapper structure
        actual_values = collected_namespace_values.get("values", {})
        if not actual_values and "_trigger" not in collected_namespace_values:
            # Backward compatibility: old format was {metric: {field: value}} directly
            actual_values = collected_namespace_values

        logger.debug(
            f"[FieldMapping] collected_namespace_values type: {type(collected_namespace_values)}, keys: {list(collected_namespace_values.keys()) if isinstance(collected_namespace_values, dict) else 'NOT DICT'}"
        )
        logger.debug(
            f"[FieldMapping] actual_values type: {type(actual_values)}, content: {actual_values}"
        )

        for metric, fields in actual_values.items():
            # Skip non-dict entries (like _trigger key that may have leaked through)
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
                if value:  # Only update if there's a value
                    field_mappings[metric][field] = value
                    logger.debug(
                        f"[FieldMapping] Merged collected value: {metric}.{field} = {value}"
                    )

        state_data["field_mappings"] = field_mappings
        logger.info(
            f"[FieldMapping] Merged {len(collected_namespace_values)} metric groups from collected values"
        )
    elif collected_namespace_values and triggered_id == "field-mapping-modal":
        logger.info(
            "[FieldMapping] Skipping merge of collected_namespace_values - modal just opened, values are stale from previous save"
        )

    # Check if state is empty or only contains profile tracking metadata and/or field_mappings
    # (state_data with only "_profile_id" and/or "field_mappings" keys should be re-initialized with other settings)
    essential_keys = {"_profile_id", "field_mappings"}
    is_partial_state = not state_data or set(state_data.keys()).issubset(essential_keys)

    # If state is partial, initialize other fields from saved settings
    # BUT preserve any field_mappings that were just merged from collected values
    if is_partial_state:
        # Preserve existing field_mappings from merge
        existing_field_mappings = state_data.get("field_mappings", {})

        # Helper to safely extract flow type mappings
        flow_mappings = settings.get("flow_type_mappings", {}) or {}

        def safe_get_flow_mapping(flow_type, key):
            """Safely extract flow mapping, handling None values."""
            flow_config = flow_mappings.get(flow_type, {})
            if flow_config is None:
                return []
            return flow_config.get(key, []) or []

        # Preserve profile ID if it exists
        profile_id = (state_data or {}).get("_profile_id")

        # Initialize state with saved settings
        state_data = {
            "_profile_id": profile_id,  # Track current profile for switch detection
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

        # Backward compatibility: prefill Estimate from jira_config if not mapped
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

        # Merge in any field_mappings collected from namespace inputs
        # These take precedence over saved settings (user just typed them)
        if existing_field_mappings:
            if "field_mappings" not in state_data:
                state_data["field_mappings"] = {}
            for metric, fields in existing_field_mappings.items():
                if isinstance(fields, dict):
                    if metric not in state_data["field_mappings"]:
                        state_data["field_mappings"][metric] = {}
                    for field, value in fields.items():
                        if value:  # Only merge non-empty values
                            state_data["field_mappings"][metric][field] = value

        logger.info("[FieldMapping] Initialized state store from saved settings")

    # Use state data for rendering (preserves user changes across tabs)
    display_settings = state_data.copy()

    # Render content based on active tab
    if active_tab == "tab-fields":
        try:
            # Check if metadata has error state
            if metadata and metadata.get("error"):
                logger.warning(
                    f"[FieldMapping] Metadata has error state: {metadata.get('error')}. "
                    "Fields tab will be empty. Check JIRA configuration."
                )
                # Return empty form - user needs to configure JIRA first
                current_mappings = {
                    "field_mappings": display_settings.get("field_mappings", {})
                }
                return create_field_mapping_form([], current_mappings), state_data

            # Use cached fields from metadata store
            cached_fields = metadata.get("fields", []) if metadata else []

            # Transform cached metadata to expected format
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

            # If no cached fields, fetch them (first time only)
            if not available_fields:
                logger.warning(
                    "[FieldMapping] No cached fields found, fetching from JIRA..."
                )
                available_fields = fetch_available_jira_fields()

            current_mappings = {
                "field_mappings": display_settings.get("field_mappings", {})
            }

            # DEBUG: Log general mappings being rendered
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
            # Return empty form with placeholder - error will be shown via toast
            # This keeps UI functional even when JIRA is not configured
            return create_field_mapping_form([], {}), state_data

    elif active_tab == "tab-projects":
        return create_project_config_form(
            development_projects=display_settings.get("development_projects", []),
            devops_projects=display_settings.get("devops_projects", []),
            available_projects=metadata.get("projects", []),
        ), state_data

    elif active_tab == "tab-types":
        # Build flow_type_mappings from state
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

        # Get effort category options
        # Priority 1: Use dynamically fetched values (from field_value_fetch callback)
        # Priority 2: Use metadata field_options (from modal open)
        available_effort_categories = []

        # Check fetched_field_values first (dynamic fetch when field changes)
        if fetched_field_values and fetched_field_values.get("effort_category"):
            available_effort_categories = fetched_field_values["effort_category"].get(
                "values", []
            )
            logger.info(
                f"[FieldMapping] Using {len(available_effort_categories)} dynamically fetched effort categories"
            )
        else:
            # Fallback to metadata field_options
            flow_field_mappings = settings.get("field_mappings", {}).get("flow", {})
            effort_category_field = flow_field_mappings.get("effort_category")
            if effort_category_field and metadata.get("field_options"):
                available_effort_categories = metadata.get("field_options", {}).get(
                    effort_category_field, []
                )
                logger.info(
                    f"[FieldMapping] Using {len(available_effort_categories)} effort categories from metadata"
                )

        available_issue_types_list = metadata.get("issue_types", [])
        logger.info(
            f"[FieldMapping] Rendering Types tab with {len(available_issue_types_list)} available issue types"
        )
        logger.info(
            f"[FieldMapping] Flow type mappings: Feature={len(flow_type_mappings.get('Feature', {}).get('issue_types', []))}, "
            f"Defect={len(flow_type_mappings.get('Defect', {}).get('issue_types', []))}, "
            f"TechnicalDebt={len(flow_type_mappings.get('Technical Debt', {}).get('issue_types', []))}, "
            f"Risk={len(flow_type_mappings.get('Risk', {}).get('issue_types', []))}"
        )

        return create_issue_type_config_form(
            devops_task_types=display_settings.get("devops_task_types", []),
            bug_types=display_settings.get("bug_types", []),
            story_types=display_settings.get("story_types", []),
            task_types=display_settings.get("task_types", []),
            available_issue_types=available_issue_types_list,
            flow_type_mappings=flow_type_mappings,
            available_effort_categories=available_effort_categories,
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
        # Get production environment field value options from affected_environment field
        # This is the field used for incident tracking and MTTR calculation
        # Note: field_mappings are nested under 'dora' and 'flow' categories
        dora_mappings = settings.get("field_mappings", {}).get("dora", {})
        affected_env_field = dora_mappings.get("affected_environment")

        available_env_values = []
        metadata_env_values = []
        fetched_env_values = []

        # Priority 1: Use field options from metadata (if field was already mapped when modal opened)
        if affected_env_field and metadata.get("field_options"):
            metadata_env_values = metadata.get("field_options", {}).get(
                affected_env_field, []
            )
            logger.debug(
                f"[FieldMapping] Loaded {len(metadata_env_values)} values from metadata.field_options[{affected_env_field}]"
            )

        # Priority 1b: Use fetched field values from store (auto-fetched when field mapping changed)
        if fetched_field_values and fetched_field_values.get("affected_environment"):
            fetched_env_values = fetched_field_values["affected_environment"].get(
                "values", []
            )
            logger.debug(
                f"[FieldMapping] Loaded {len(fetched_env_values)} values from fetched-field-values-store"
            )

        # Combine metadata and fetched values
        available_env_values = list(set(metadata_env_values + fetched_env_values))

        # Priority 2: Use field_values from state (populated by auto-configure from issue analysis)
        if not available_env_values:
            field_values = (state_data or {}).get("field_values", {})
            if field_values and "target_environment" in field_values:
                available_env_values = field_values["target_environment"]
                # Limit to first 50 values to prevent browser performance issues
                if len(available_env_values) > 50:
                    logger.warning(
                        f"[FieldMapping] Truncating environment values from {len(available_env_values)} to 50"
                    )
                    available_env_values = available_env_values[:50]
                logger.debug(
                    f"[FieldMapping] Loaded {len(available_env_values)} values from state_data.field_values.target_environment"
                )

        # Priority 3: Use auto-detected production identifiers from metadata as options
        # (at minimum, show these so user can select from them)
        if not available_env_values:
            auto_detected = (metadata or {}).get("auto_detected", {})
            prod_identifiers = auto_detected.get("production_identifiers", [])
            if prod_identifiers:
                available_env_values = prod_identifiers
                logger.debug(
                    f"[FieldMapping] Using {len(available_env_values)} auto-detected production identifiers as options"
                )

        return create_environment_config_form(
            production_environment_values=display_settings.get(
                "production_environment_values", []
            ),
            available_environment_values=available_env_values,
        ), state_data

    return html.Div("Select a tab to configure mappings."), state_data
