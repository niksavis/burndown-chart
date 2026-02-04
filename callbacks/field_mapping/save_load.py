"""Save and validate field mappings.

Handles the complex save/validate logic for all field mapping configurations
across all tabs with comprehensive validation.
"""

import logging
from dash import callback, Output, Input, State, no_update
from ui.toast_notifications import create_success_toast, create_error_toast
from callbacks.field_mapping.validation_helpers import (
    _validate_all_tabs,
    _build_comprehensive_validation_alert,
    _build_validation_error_alert,
)

logger = logging.getLogger(__name__)


@callback(
    [
        Output("field-mapping-save-success", "data", allow_duplicate=True),
        Output("field-mapping-status", "children", allow_duplicate=True),
        Output("field-mapping-state-store", "data", allow_duplicate=True),
        Output("app-notifications", "children", allow_duplicate=True),
        Output("metrics-refresh-trigger", "data", allow_duplicate=True),
    ],
    Input("namespace-collected-values", "data"),
    State("field-mapping-state-store", "data"),
    prevent_initial_call=True,
    priority=1,  # Higher priority ensures this runs after other status updates
)
def save_or_validate_mappings(namespace_values, state_data):
    """Save, validate, or update state from collected namespace values.

    This callback handles "save", "validate", and "tab_switch" triggers from the
    clientside collectNamespaceValues function. The trigger type determines
    the action:

    - trigger="validate": Validates and shows results in modal (no save)
    - trigger="save": Validates, then saves if valid
    - trigger="tab_switch": Updates state store with collected values (preserves them)

    Values are collected by a clientside callback (collectNamespaceValues)
    that reads directly from the DOM and stores them in namespace-collected-values.

    Args:
        namespace_values: Collected values with trigger info from clientside callback
        state_data: Current form state from state store

    Returns:
        Tuple of (save_success, status_message, updated_state, toast_notification, metrics_refresh_trigger)
        - save_success: True if save succeeded, False if failed, no_update otherwise
        - status_message: Status alert HTML or no_update
        - updated_state: Updated state store data or no_update
        - toast_notification: Toast notification HTML or no_update
        - metrics_refresh_trigger: Timestamp to trigger metrics refresh (on save success), no_update otherwise
    """
    from data.persistence import save_app_settings, load_app_settings

    # namespace_values has structure: {trigger: "save"|"validate"|"tab_switch", values: {...}, validationErrors: [...]}
    if not namespace_values or not isinstance(namespace_values, dict):
        return no_update, no_update, no_update, no_update, no_update

    trigger = namespace_values.get("trigger", "")
    collected_values = namespace_values.get("values", {})
    validation_errors = namespace_values.get("validationErrors", [])

    # Handle TAB_SWITCH trigger - just update state store with collected values
    if trigger == "tab_switch":
        if not collected_values:
            return no_update, no_update, no_update, no_update, no_update

        # Merge collected namespace values into state_data
        state_data = (state_data or {}).copy()
        if "field_mappings" not in state_data:
            state_data["field_mappings"] = {}

        for metric, fields in collected_values.items():
            if not isinstance(fields, dict):
                continue
            if metric not in state_data["field_mappings"]:
                state_data["field_mappings"][metric] = {}
            for field, value in fields.items():
                if value and str(value).strip():
                    state_data["field_mappings"][metric][field] = str(value).strip()

        logger.info(
            f"[FieldMapping] Tab switch - saved {len(collected_values)} metric groups to state"
        )
        return no_update, no_update, state_data, no_update, no_update

    # Handle VALIDATE trigger - comprehensive validation across all tabs
    if trigger == "validate":
        # Merge collected field values into state for comprehensive validation
        state_with_fields = (state_data or {}).copy()

        # Log what we're starting with
        logger.info(
            f"[FieldMapping] VALIDATE - state_data field_mappings: {state_data.get('field_mappings', {}) if state_data else 'None'}"
        )
        logger.info(f"[FieldMapping] VALIDATE - collected_values: {collected_values}")

        # Always initialize field_mappings structure
        if "field_mappings" not in state_with_fields:
            state_with_fields["field_mappings"] = {}

        # If we have collected values from the Fields tab, use them as the source of truth
        # Otherwise, keep existing state_data values (user might be validating from another tab)
        if collected_values and isinstance(collected_values, dict):
            # Process ALL metric sections (dora, flow, general) to ensure cleared fields are detected
            for metric in ["dora", "flow", "general"]:
                # Clear the metric section first
                state_with_fields["field_mappings"][metric] = {}
                # Repopulate with collected values if present
                if metric in collected_values:
                    fields = collected_values[metric]
                    for field, value in fields.items():
                        if value and str(value).strip():
                            state_with_fields["field_mappings"][metric][field] = value

        # Log what we're validating with
        logger.info(
            f"[FieldMapping] VALIDATE - state_with_fields field_mappings after merge: {state_with_fields.get('field_mappings', {})}"
        )

        # Run comprehensive validation across all tabs
        validation_result = _validate_all_tabs(state_with_fields, validation_errors)

        logger.info(
            f"[FieldMapping] Comprehensive validation: "
            f"valid={validation_result['is_valid']}, "
            f"errors={len(validation_result['errors'])}, "
            f"warnings={len(validation_result['warnings'])}, "
            f"summary={validation_result['summary']}"
        )

        return (
            no_update,
            _build_comprehensive_validation_alert(validation_result),
            no_update,
            no_update,  # Validation uses inline alert (keeps validation in modal)
            no_update,  # Don't refresh metrics on validation
        )

    # Handle SAVE trigger
    if trigger != "save":
        # Unknown trigger - ignore
        logger.info(
            f"[FieldMapping] Unknown trigger detected, ignoring (trigger={trigger})"
        )
        return no_update, no_update, no_update, no_update, no_update

    # Check for clientside validation errors - reject save if any invalid values
    if validation_errors:
        logger.warning(
            f"[FieldMapping] Save rejected due to clientside validation errors: {validation_errors}"
        )
        return (
            False,
            _build_validation_error_alert(validation_errors),
            no_update,
            no_update,
            no_update,
        )

    # CRITICAL: Run comprehensive server-side validation before save
    # This includes checks for WIP/completion overlap and other logical errors
    state_with_fields = (state_data or {}).copy()
    if collected_values:
        if "field_mappings" not in state_with_fields:
            state_with_fields["field_mappings"] = {}
        # Process ALL metric sections (dora, flow, general) to ensure cleared fields are detected
        for metric in ["dora", "flow", "general"]:
            # Clear the metric section first
            state_with_fields["field_mappings"][metric] = {}
            # Repopulate with collected values if present
            if metric in collected_values:
                fields = collected_values[metric]
                for field, value in fields.items():
                    if value and str(value).strip():
                        state_with_fields["field_mappings"][metric][field] = value

    validation_result = _validate_all_tabs(state_with_fields, validation_errors)

    # Block save if there are server-side errors
    if not validation_result["is_valid"]:
        logger.warning(
            f"[FieldMapping] Save rejected due to server-side validation errors: "
            f"{len(validation_result['errors'])} error(s)"
        )
        toast = create_error_toast(
            f"Configuration has {len(validation_result['errors'])} error(s) that must be fixed before saving. "
            f"Click 'Validate' to see details.",
            header="Validation Failed",
            duration=8000,
        )
        return (
            False,
            _build_comprehensive_validation_alert(validation_result),
            no_update,
            toast,
            no_update,
        )

    # Log warnings but allow save
    if validation_result["warnings"]:
        logger.info(
            f"[FieldMapping] Saving with {len(validation_result['warnings'])} warning(s)"
        )

    # Check JIRA configuration exists before allowing save
    settings = load_app_settings()
    jira_config = settings.get("jira_config", {})
    # Only base_url is required - token is optional for public JIRA servers
    has_jira_config = bool(jira_config.get("base_url"))

    if not has_jira_config:
        logger.warning("[FieldMapping] Save rejected - JIRA configuration not set up")
        toast = create_error_toast(
            "Please configure JIRA connection first (URL) in the Settings panel.",
            header="JIRA Not Configured",
        )
        return False, "", no_update, toast, no_update

    # Check if there's at least one meaningful field mapping in CURRENT form values
    # Check BOTH collected_values (namespace inputs) AND state_data (dropdown configs)
    total_mapped_fields = 0

    # Check namespace field mappings (Fields tab)
    if collected_values and isinstance(collected_values, dict):
        for metric in ["dora", "flow", "general"]:  # Include general fields
            if metric in collected_values:
                for value in collected_values[metric].values():
                    if value and str(value).strip():
                        total_mapped_fields += 1

    # Check state_data for dropdown-based configurations (Types, Status, Projects, Environment tabs)
    if state_data and isinstance(state_data, dict):
        # Count projects (development and devops)
        dev_projects = state_data.get("development_projects", [])
        devops_projects = state_data.get("devops_projects", [])
        total_mapped_fields += len([p for p in (dev_projects + devops_projects) if p])

        # Count issue types (DORA)
        devops_types = state_data.get("devops_task_types", [])
        bug_types = state_data.get("bug_types", [])
        total_mapped_fields += len([t for t in (devops_types + bug_types) if t])

        # Count flow type mappings
        flow_type_mappings = state_data.get("flow_type_mappings", {})
        for flow_type, config in flow_type_mappings.items():
            if config and isinstance(config, dict):
                issue_types = config.get("issue_types", [])
                effort_cats = config.get("effort_categories", [])
                total_mapped_fields += len([t for t in issue_types if t])
                total_mapped_fields += len([c for c in effort_cats if c])

        # Count statuses
        flow_end = state_data.get("flow_end_statuses", [])
        active = state_data.get("active_statuses", [])
        flow_start = state_data.get("flow_start_statuses", [])
        wip = state_data.get("wip_statuses", [])
        total_mapped_fields += len(
            [s for s in (flow_end + active + flow_start + wip) if s]
        )

        # Count environment values
        prod_env = state_data.get("production_environment_values", [])
        total_mapped_fields += len([e for e in prod_env if e])

    if total_mapped_fields == 0:
        logger.warning(
            "[FieldMapping] Save rejected - no field mappings configured in current form"
        )
        toast = create_error_toast(
            "Please configure at least one field mapping before saving.",
            header="No Mappings Configured",
        )
        return False, "", no_update, toast, no_update

    logger.info(
        f"[FieldMapping] Validation passed with {total_mapped_fields} configured values"
    )

    # CRITICAL: Invalidate metrics cache after validation passes, before save
    # This ensures metrics are recalculated with new config on next Update Data
    # Only invalidated if validation succeeds - avoids clearing cache for rejected changes
    # Affects ALL field mappings: status configs, project filters, issue types, environment values, etc.
    try:
        from data.persistence.factory import get_backend
        from data.metrics_snapshots import clear_snapshots_cache

        backend = get_backend()
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if active_profile_id and active_query_id:
            deleted_count = backend.delete_metrics(active_profile_id, active_query_id)
            # ALSO clear in-memory snapshots cache (used by Flow/DORA metrics display)
            clear_snapshots_cache()
            logger.info(
                f"[FieldMapping] Invalidated metrics cache after validation ({deleted_count} records deleted, in-memory cache cleared)"
            )
    except Exception as cache_error:
        # Non-fatal but log it - metrics will eventually be recalculated
        logger.warning(
            f"[FieldMapping] Failed to invalidate metrics cache: {cache_error}"
        )

    # DEBUG: Log what we're about to save
    logger.info(
        f"[FieldMapping] state_data keys: {list(state_data.keys()) if state_data else 'None'}"
    )
    logger.info(
        f"[FieldMapping] collected_values keys: {list(collected_values.keys()) if collected_values else 'None'}"
    )
    if state_data:
        logger.info(
            f"[FieldMapping] development_projects: {state_data.get('development_projects')}"
        )
        logger.info(
            f"[FieldMapping] devops_task_types: {state_data.get('devops_task_types')}"
        )
        logger.info(
            f"[FieldMapping] flow_end_statuses: {state_data.get('flow_end_statuses')}"
        )
        logger.info(f"[FieldMapping] wip_statuses: {state_data.get('wip_statuses')}")

    try:
        # Settings already loaded above
        state_data = state_data or {}

        # Use values collected by clientside callback from namespace inputs
        if collected_values and isinstance(collected_values, dict):
            logger.info(f"[FieldMapping] Saving namespace values: {collected_values}")
            logger.info(
                f"[FieldMapping] Metrics in collected_values: {list(collected_values.keys())}"
            )
            # Build field_mappings from namespace input values
            state_data = state_data or {}
            if "field_mappings" not in state_data:
                state_data["field_mappings"] = {}

            # Process ALL metric sections (dora, flow, general) - not just those in collected_values
            # This ensures that when ALL fields in a metric are cleared (clientside doesn't collect empty metrics),
            # the metric gets properly cleared instead of preserving old values from state_data
            for metric in ["dora", "flow", "general"]:
                # Clear the metric section first
                state_data["field_mappings"][metric] = {}

                # Repopulate with collected values if present
                if metric in collected_values:
                    fields = collected_values[metric]
                    for field, value in fields.items():
                        if value and str(value).strip():
                            state_data["field_mappings"][metric][field] = str(
                                value
                            ).strip()
                            logger.info(
                                f"[FieldMapping] Saved namespace value: {metric}.{field} = {value}"
                            )
                else:
                    logger.info(
                        f"[FieldMapping] Metric '{metric}' not in collected values - cleared to empty"
                    )

            # DEBUG: Log general mappings after processing collected values
            general_mappings_after = state_data.get("field_mappings", {}).get(
                "general", {}
            )
            logger.info(
                f"[FieldMapping] General mappings after collection: {general_mappings_after}"
            )

        # Update settings from state store
        # Field mappings
        if "field_mappings" in state_data:
            # Store raw namespace strings WITHOUT parsing to SourceRule
            # Parsing should happen at metric calculation time, not save time
            # This ensures the UI can display the original namespace syntax
            raw_field_mappings = state_data["field_mappings"]
            settings["field_mappings"] = raw_field_mappings

            # DEBUG: Log general mappings being saved
            general_in_raw = raw_field_mappings.get("general", {})
            logger.info(
                f"[FieldMapping] Saving field mappings - DORA: {len(raw_field_mappings.get('dora', {}))}, "
                f"Flow: {len(raw_field_mappings.get('flow', {}))}, "
                f"General: {len(general_in_raw)} fields = {list(general_in_raw.keys())}"
            )
        else:
            logger.warning(
                "[FieldMapping] Field mappings not found in state - state may be empty"
            )

        # CRITICAL: Add parent_issue_types to field_mappings.general (from Types tab dropdown)
        # This enables query_builder to include parent types in JQL query
        if "parent_issue_types" in state_data:
            if "field_mappings" not in settings:
                settings["field_mappings"] = {}
            if "general" not in settings["field_mappings"]:
                settings["field_mappings"]["general"] = {}
            settings["field_mappings"]["general"]["parent_issue_types"] = state_data[
                "parent_issue_types"
            ]
            logger.info(
                f"[FieldMapping] Saved parent_issue_types to field_mappings.general: {state_data['parent_issue_types']}"
            )

        # Read from nested project_classification structure (NEW format from auto-configure)
        if "project_classification" in state_data:
            proj_class = state_data["project_classification"]
            settings["development_projects"] = proj_class.get(
                "development_projects", []
            )
            settings["devops_projects"] = proj_class.get("devops_projects", [])
            settings["flow_end_statuses"] = proj_class.get("flow_end_statuses", [])
            settings["active_statuses"] = proj_class.get("active_statuses", [])
            settings["flow_start_statuses"] = proj_class.get("flow_start_statuses", [])
            settings["wip_statuses"] = proj_class.get("wip_statuses", [])

        # Read from nested flow_type_mappings structure (NEW format from auto-configure)
        if "flow_type_mappings" in state_data:
            settings["flow_type_mappings"] = state_data["flow_type_mappings"]

        # Fallback: Also check old flat keys for backward compatibility
        if "development_projects" in state_data:
            settings["development_projects"] = state_data["development_projects"]
            logger.info(
                f"[FieldMapping DEBUG] Found development_projects in state: {settings['development_projects']}"
            )
        if "devops_projects" in state_data:
            settings["devops_projects"] = state_data["devops_projects"]
            logger.info(
                f"[FieldMapping DEBUG] Found devops_projects in state: {settings['devops_projects']}"
            )

        # CRITICAL DEBUG: Log what will be saved
        logger.info(
            f"[FieldMapping DEBUG] About to save - development_projects: {settings.get('development_projects', [])}, devops_projects: {settings.get('devops_projects', [])}"
        )
        if "flow_end_statuses" in state_data:
            settings["flow_end_statuses"] = state_data["flow_end_statuses"]
        if "active_statuses" in state_data:
            settings["active_statuses"] = state_data["active_statuses"]
        if "flow_start_statuses" in state_data:
            settings["flow_start_statuses"] = state_data["flow_start_statuses"]
        if "wip_statuses" in state_data:
            settings["wip_statuses"] = state_data["wip_statuses"]

        # Fallback: Old flow type keys (kept for backward compatibility with manual edits)
        if (
            "flow_feature_issue_types" in state_data
            or "flow_defect_issue_types" in state_data
        ):
            flow_type_mappings = {
                "Feature": {
                    "issue_types": state_data.get("flow_feature_issue_types", []),
                    "effort_categories": state_data.get(
                        "flow_feature_effort_categories", []
                    ),
                },
                "Defect": {
                    "issue_types": state_data.get("flow_defect_issue_types", []),
                    "effort_categories": state_data.get(
                        "flow_defect_effort_categories", []
                    ),
                },
                "Technical Debt": {
                    "issue_types": state_data.get(
                        "flow_technical_debt_issue_types", []
                    ),
                    "effort_categories": state_data.get(
                        "flow_technical_debt_effort_categories", []
                    ),
                },
                "Risk": {
                    "issue_types": state_data.get("flow_risk_issue_types", []),
                    "effort_categories": state_data.get(
                        "flow_risk_effort_categories", []
                    ),
                },
            }
            settings["flow_type_mappings"] = flow_type_mappings

        # Issue Types (old flat structure - kept for backward compatibility)
        if "devops_task_types" in state_data:
            settings["devops_task_types"] = state_data["devops_task_types"]
        if "bug_types" in state_data:
            settings["bug_types"] = state_data["bug_types"]
        if "story_types" in state_data:
            settings["story_types"] = state_data["story_types"]
        if "task_types" in state_data:
            settings["task_types"] = state_data["task_types"]

        # Environment
        if "production_environment_values" in state_data:
            settings["production_environment_values"] = state_data[
                "production_environment_values"
            ]

        # Points field - read from General > Estimate mapping, stored in jira_config
        estimate_field = (
            settings.get("field_mappings", {}).get("general", {}).get("estimate", "")
        )
        if "jira_config" not in settings:
            settings["jira_config"] = {}
        settings["jira_config"]["points_field"] = (
            estimate_field.strip() if isinstance(estimate_field, str) else ""
        )
        logger.info(
            "[FieldMapping] Updated points_field in jira_config from Estimate mapping"
        )

        # Save to disk - extract individual parameters from settings dict
        save_app_settings(
            pert_factor=settings.get("pert_factor", 1.2),
            deadline=settings.get("deadline"),
            data_points_count=settings.get("data_points_count"),
            show_milestone=settings.get("show_milestone"),
            milestone=settings.get("milestone"),
            show_points=settings.get("show_points"),
            jql_query=settings.get("jql_query"),
            last_used_data_source=settings.get("last_used_data_source"),
            active_jql_profile_id=settings.get("active_jql_profile_id"),
            jira_config=settings.get("jira_config"),
            field_mappings=settings.get("field_mappings"),
            development_projects=settings.get("development_projects"),
            devops_projects=settings.get("devops_projects"),
            devops_task_types=settings.get("devops_task_types"),
            bug_types=settings.get("bug_types"),
            story_types=settings.get("story_types"),
            task_types=settings.get("task_types"),
            production_environment_values=settings.get("production_environment_values"),
            flow_end_statuses=settings.get("flow_end_statuses"),
            active_statuses=settings.get("active_statuses"),
            flow_start_statuses=settings.get("flow_start_statuses"),
            wip_statuses=settings.get("wip_statuses"),
            flow_type_mappings=settings.get("flow_type_mappings"),
            cache_metadata=settings.get("cache_metadata"),
        )

        logger.info("[FieldMapping] Mappings saved successfully from state store")

        # Success toast notification
        toast = create_success_toast(
            "Your field mappings and configurations have been saved.",
            header="Configuration Saved",
        )

        # Update state store with saved values so modal shows correct state when reopened
        # Trigger metrics refresh to show "No metrics" state immediately
        import time

        return True, "", state_data, toast, time.time()

    except Exception as e:
        logger.error(f"[FieldMapping] Error saving mappings: {e}")
        toast = create_error_toast(
            f"Error saving mappings: {str(e)}",
            header="Save Failed",
        )
        return False, "", no_update, toast, no_update
