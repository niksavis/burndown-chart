@callback(
    [
        Output("field-mapping-state-store", "data", allow_duplicate=True),
        Output("field-mapping-status", "children", allow_duplicate=True),
        Output("auto-configure-warning-banner", "is_open", allow_duplicate=True),
        Output("auto-configure-refresh-trigger", "data"),  # Trigger tab re-render
        Output("auto-configure-confirm-button", "disabled"),
        Output("auto-configure-confirm-button", "children"),
        Output("app-notifications", "children", allow_duplicate=True),
    ],
    Input("auto-configure-confirm-button", "n_clicks"),
    [
        State("jira-metadata-store", "data"),
        State("field-mapping-state-store", "data"),
        State(
            "auto-configure-refresh-trigger", "data"
        ),  # Get current value to increment
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
    n_clicks: int, metadata: Dict, current_state: Dict, current_trigger: int
):
    """Auto-configure profile settings from JIRA metadata.

    Generates smart defaults for all configuration sections:
    - Project classification (completion/active/WIP statuses)
    - Flow type mappings (Feature/Defect/TechnicalDebt/Risk)
    - Development projects (extracted from JQL query)

    Args:
        n_clicks: Number of times auto-configure button clicked
        metadata: JIRA metadata from jira-metadata-store
        current_state: Current state from state store

    Returns:
        Tuple of (updated_state, status_alert, banner_closed)
    """
    from data.auto_configure import generate_smart_defaults
    from data.profile_manager import get_active_profile, get_profile_file_path
    import json

    if not n_clicks:
        return (
            no_update,
            no_update,
            no_update,
            no_update,  # Don't trigger refresh
            no_update,  # Button disabled state
            no_update,  # Button children
            no_update,  # Toast notification
        )

    try:
        # Validate metadata is available
        if not metadata or metadata.get("error"):
            return (
                no_update,
                "",  # Clear inline status
                False,  # Close confirmation modal
                no_update,  # Don't trigger refresh on error
                False,  # Re-enable button
                [html.I(className="fas fa-check me-2"), "Yes, Auto-Configure Now"],
                create_error_toast(
                    "JIRA metadata not available. Please ensure JIRA is connected.",
                    header="Cannot Auto-Configure",
                ),
            )

        # Get active profile to extract JQL query
        active_profile = get_active_profile()
        if not active_profile:
            return (
                no_update,
                "",  # Clear inline status
                False,  # Close confirmation modal
                no_update,  # Don't trigger refresh on error
                False,  # Re-enable button
                [html.I(className="fas fa-check me-2"), "Yes, Auto-Configure Now"],
                create_error_toast(
                    "No active profile found.",
                    header="Cannot Auto-Configure",
                ),
            )

        profile_id = active_profile.id
        profile_path = get_profile_file_path(profile_id)

        # Load current profile to get active query JQL
        jql_query = None
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                profile_data = json.load(f)

                # Get active query ID from profile
                active_query_id = profile_data.get("active_query_id")

                # Fallback: If no active query, check if there are any queries
                if not active_query_id:
                    queries = profile_data.get("queries", [])
                    if queries and len(queries) > 0:
                        active_query_id = (
                            queries[0].get("id")
                            if isinstance(queries[0], dict)
                            else queries[0]
                        )
                        logger.info(
                            f"[AutoConfigure] No active query, using first query: {active_query_id}"
                        )
                    else:
                        # Last resort: Check for query directories
                        from pathlib import Path

                        queries_dir = Path(profile_path).parent / "queries"
                        if queries_dir.exists():
                            query_dirs = [
                                d for d in queries_dir.iterdir() if d.is_dir()
                            ]
                            if query_dirs:
                                active_query_id = query_dirs[0].name
                                logger.info(
                                    f"[AutoConfigure] Found query directory: {active_query_id}"
                                )

                if active_query_id:
                    # Load query from database
                    from data.persistence.factory import get_backend

                    backend = get_backend()

                    try:
                        query_data = backend.get_query(profile_id, active_query_id)
                        if query_data:
                            jql_query = query_data.get("jql", "")
                            logger.info(
                                f"[AutoConfigure] Loaded JQL query from active query: {jql_query}"
                            )
                        else:
                            logger.warning(
                                f"[AutoConfigure] Query {active_query_id} not found in database"
                            )
                    except Exception as qe:
                        logger.warning(f"Could not load query from database: {qe}")
                else:
                    logger.warning(
                        "No active query ID found in profile and no fallback queries available"
                    )
        except Exception as e:
            logger.warning(f"Could not load profile data: {e}")

        logger.info(
            f"[AutoConfigure] Generating smart defaults for profile {profile_id}"
        )

        # Fetch recent issues for field detection (last 100 issues)
        issues = []
        if jql_query:
            try:
                from data.jira import fetch_jira_issues

                logger.info(
                    "[AutoConfigure] Fetching last 100 issues for field analysis..."
                )
                # Modify JQL to get last 100 issues ordered by created date
                sample_jql = f"{jql_query} ORDER BY created DESC"

                # Get JIRA config from profile
                with open(profile_path, "r", encoding="utf-8") as f:
                    profile_data = json.load(f)
                    jira_config = profile_data.get("jira_config", {})

                # Build config dict for fetch_jira_issues (matches expected structure)
                fetch_config = {
                    "jql_query": sample_jql,
                    "api_endpoint": jira_config.get("base_url", "").rstrip("/")
                    + "/rest/api/2/search",
                    "token": jira_config.get("token", ""),
                    "story_points_field": jira_config.get("points_field", ""),
                    "field_mappings": {},  # Empty for field detection - we want ALL fields
                    "fields": "*all",  # CRITICAL: Request ALL fields including custom fields
                }

                # Fetch issues
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

        # Generate smart defaults using metadata and issues
        defaults = generate_smart_defaults(metadata, jql_query, issues)

        # Update state store with auto-configured values
        new_state = current_state.copy() if current_state else {}

        # CRITICAL: Store values in FLAT keys that the UI dropdowns read from
        # The render_tab_content callback reads from these flat keys to populate dropdowns
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

        # Flow type mappings - store in flat keys for UI
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

        # Bug types - store in flat key for UI (Incident Types dropdown)
        if (
            "project_classification" in defaults
            and "bug_types" in defaults["project_classification"]
        ):
            new_state["bug_types"] = defaults["project_classification"]["bug_types"]
            logger.info(
                f"[AutoConfigure] Stored {len(new_state['bug_types'])} incident types for UI"
            )

        # DevOps task types - store in flat key for UI (DevOps Task Types dropdown)
        if (
            "project_classification" in defaults
            and "devops_task_types" in defaults["project_classification"]
        ):
            new_state["devops_task_types"] = defaults["project_classification"][
                "devops_task_types"
            ]
            logger.info(
                f"[AutoConfigure] Stored {len(new_state['devops_task_types'])} DevOps task types for UI"
            )

        # Field mappings - store if detected (DORA + Flow only)
        if "field_mappings" in defaults:
            new_state["field_mappings"] = defaults["field_mappings"]

        # Points field - store in General Fields mapping (Estimate)
        if "points_field" in defaults:
            if "field_mappings" not in new_state:
                new_state["field_mappings"] = {}
            if "general" not in new_state["field_mappings"]:
                new_state["field_mappings"]["general"] = {}
            new_state["field_mappings"]["general"]["estimate"] = defaults[
                "points_field"
            ]

        # Field values - store for dropdown population
        if "field_values" in defaults:
            new_state["field_values"] = defaults["field_values"]

        # ALSO store in nested structure for profile.json compatibility
        if "project_classification" not in new_state:
            new_state["project_classification"] = {}
        new_state["project_classification"].update(defaults["project_classification"])

        # Populate production_environment_values from auto-detected production identifiers
        # These are values matching patterns like "prod", "production", "live", "prd"
        auto_detected_prod = (
            metadata.get("auto_detected", {}).get("production_identifiers", [])
            if metadata
            else []
        )
        if auto_detected_prod:
            # Use auto-detected production identifiers for pre-selection
            new_state["project_classification"]["production_environment_values"] = (
                auto_detected_prod
            )
            new_state["production_environment_values"] = auto_detected_prod
            logger.info(
                f"[AutoConfigure] Pre-selected {len(auto_detected_prod)} auto-detected production identifiers: {auto_detected_prod}"
            )
        elif (
            "field_values" in defaults
            and "target_environment" in defaults["field_values"]
        ):
            # Fallback: If no auto-detected values, don't pre-select anything
            # The dropdown will show all available values for manual selection
            logger.info(
                f"[AutoConfigure] No auto-detected production identifiers found. "
                f"Available environment values: {len(defaults['field_values']['target_environment'])}"
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

            # Populate effort_categories from field_values if available
            if (
                "field_values" in defaults
                and "effort_category" in defaults["field_values"]
            ):
                new_state["flow_type_mappings"][flow_type]["effort_categories"] = (
                    defaults["field_values"]["effort_category"]
                )
                logger.info(
                    f"[AutoConfigure] Populated {len(defaults['field_values']['effort_category'])} effort categories for {flow_type}"
                )

        # Count what was configured
        completion_count = len(defaults["project_classification"]["flow_end_statuses"])
        active_count = len(defaults["project_classification"]["active_statuses"])
        wip_count = len(defaults["project_classification"]["wip_statuses"])
        feature_count = len(defaults["flow_type_mappings"]["Feature"])
        defect_count = len(defaults["flow_type_mappings"]["Defect"])
        project_count = len(defaults["project_classification"]["development_projects"])

        logger.info(
            f"[AutoConfigure] Generated defaults: {completion_count} completion, "
            f"{active_count} active, {wip_count} WIP statuses, "
            f"{feature_count} features, {defect_count} defects, {project_count} projects"
        )

        # Create success toast notification
        total_statuses = completion_count + active_count + wip_count
        total_types = feature_count + defect_count
        toast = create_success_toast(
            f"{total_statuses} statuses, {total_types} work types, "
            f"{project_count} project{'s' if project_count != 1 else ''}. "
            "Click 'Save Mappings' to apply.",
            header="Auto-Configuration Complete",
            duration=5000,
        )

        # Increment refresh trigger to force tab re-render with new state
        new_trigger = (current_trigger or 0) + 1
        return (
            new_state,
            "",  # Clear inline status
            False,
            new_trigger,
            False,  # Re-enable button
            [html.I(className="fas fa-check me-2"), "Yes, Auto-Configure Now"],
            toast,
        )  # Close modal, trigger refresh

    except Exception as e:
        logger.error(
            f"[AutoConfigure] Error during auto-configuration: {e}", exc_info=True
        )
        return (
            no_update,
            "",  # Clear inline status
            False,
            no_update,
            False,  # Re-enable button
            [html.I(className="fas fa-check me-2"), "Yes, Auto-Configure Now"],
            create_error_toast(f"Error: {str(e)}", header="Auto-Configuration Failed"),
        )  # Close modal, don't trigger refresh


# ============================================================================
# VALIDATE AND SAVE MAPPINGS
# ============================================================================


