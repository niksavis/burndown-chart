"""Callbacks for profile import/export functionality."""

from datetime import datetime
import json
import logging
import time
from dash import (
    callback,
    Output,
    Input,
    State,
    no_update,
    clientside_callback,
    ClientsideFunction,
)
from data.query_manager import get_active_profile_id, get_active_query_id

logger = logging.getLogger(__name__)

# Note: Report generation callbacks moved to callbacks/report_generation.py


@callback(
    Output("export-profile-download", "data"),
    Output("app-notifications", "children", allow_duplicate=True),
    Input("export-profile-button", "n_clicks"),
    State("export-mode-radio", "value"),
    State("include-token-checkbox", "value"),
    State("include-budget-checkbox", "value"),
    prevent_initial_call=True,
)
def export_full_profile(n_clicks, export_mode, include_token, include_budget):
    """Export profile with mode selection and optional token inclusion (T013)."""
    from ui.toast_notifications import create_toast

    if not n_clicks:
        return no_update, no_update

    try:
        profile_id = get_active_profile_id()
        query_id = get_active_query_id()

        if not profile_id or not query_id:
            logger.error("No active profile/query for export")
            return no_update, create_toast(
                "Export Failed", "No active profile or query selected", "danger"
            )

        # Use new T013 export function
        from data.import_export import export_profile_with_mode

        export_package = export_profile_with_mode(
            profile_id=profile_id,
            query_id=query_id,
            export_mode=export_mode or "CONFIG_ONLY",
            include_token=bool(include_token),
            include_budget=bool(include_budget),
        )

        # Generate filename (matches report format for easy archiving)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        profile_name = profile_id.replace(" ", "_").replace("/", "_")
        query_name = query_id.replace(" ", "_").replace("/", "_")

        # Export mode descriptor
        mode_suffix = "config_only" if export_mode == "CONFIG_ONLY" else "full_data"

        # Token inclusion indicator (only add if token included)
        token_suffix = "_with_token" if bool(include_token) else ""

        # Format: YYYYMMDD_HHMMSS_Profile_Query_export_MODE[_with_token].json
        filename = f"{timestamp}_{profile_name}_{query_name}_export_{mode_suffix}{token_suffix}.json"

        # Convert to JSON string
        json_content = json.dumps(export_package, indent=2, ensure_ascii=False)
        file_size_kb = len(json_content) / 1024

        # User-friendly mode names
        mode_display = (
            "Configuration only" if export_mode == "CONFIG_ONLY" else "Full data"
        )

        logger.info(
            f"Exported profile/query data: {file_size_kb:.1f} KB, mode={export_mode}, token={include_token}"
        )

        # Return download trigger and success toast
        return (
            {"content": json_content, "filename": filename},
            create_toast(
                f"Profile exported successfully ({file_size_kb:.1f} KB). Mode: {mode_display}",
                toast_type="success",
                header="Export Successful",
                duration=4000,
            ),
        )

    except Exception as e:
        logger.error(f"Profile export failed: {e}", exc_info=True)
        return no_update, create_toast(
            "Export Failed", f"Could not export profile: {str(e)}", "danger"
        )


@callback(
    Output("conflict-resolution-modal", "is_open"),
    Output("conflict-profile-name", "children"),
    Output("import-data-store", "data"),  # Store for later use
    Output("conflict-rename-input", "placeholder"),  # Suggest a name
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    prevent_initial_call=True,
)
def detect_import_conflict(contents, filename):
    """T051: Detect profile conflicts and show resolution modal."""
    if not contents:
        return no_update, no_update, no_update, no_update

    try:
        # Decode uploaded file
        import base64

        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        import_data = json.loads(decoded.decode("utf-8"))

        # Get profile data from new format
        profile_data = import_data.get("profile_data", {})
        profile_id = profile_data.get("id") or import_data.get("profile_id")
        profile_name = profile_data.get("name", profile_id)

        if not profile_id:
            return False, "", None, no_update

        # Check if profile already exists in database
        from data.persistence.factory import get_backend

        backend = get_backend()
        existing_profile = backend.get_profile(profile_id)

        if existing_profile:
            # Conflict detected - show modal with profile name
            logger.info(
                f"Import conflict detected: Profile '{profile_id}' already exists"
            )
            # Suggest a default name for rename option
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            suggested_name = f"{profile_id}_{timestamp}"
            return True, profile_name, import_data, suggested_name
        else:
            # No conflict - proceed with import directly
            logger.info(
                f"No conflict detected for profile '{profile_id}' - proceeding with import"
            )
            return False, "", import_data, no_update

    except Exception as e:
        logger.error(f"Conflict detection failed: {e}", exc_info=True)
        return False, "", None, no_update


@callback(
    Output("app-notifications", "children", allow_duplicate=True),
    Output("metrics-refresh-trigger", "data", allow_duplicate=True),
    Output("profile-switch-trigger", "data", allow_duplicate=True),
    Output("upload-data", "contents", allow_duplicate=True),
    Input("import-data-store", "data"),
    State("conflict-resolution-modal", "is_open"),
    prevent_initial_call=True,
)
def import_without_conflict(import_data, modal_is_open):
    """T051: Handle import when no conflict exists (direct import)."""
    # Only proceed if modal is NOT open (no conflict detected)
    if not import_data or modal_is_open:
        return no_update, no_update, no_update, no_update
    toast, refresh, profile_switch = perform_import(import_data)
    return toast, refresh, profile_switch, None  # Clear upload contents


@callback(
    Output("app-notifications", "children", allow_duplicate=True),
    Output("conflict-resolution-modal", "is_open", allow_duplicate=True),
    Output("metrics-refresh-trigger", "data", allow_duplicate=True),
    Output("profile-switch-trigger", "data", allow_duplicate=True),
    Output("upload-data", "contents", allow_duplicate=True),
    Input("conflict-proceed", "n_clicks"),
    Input("conflict-cancel", "n_clicks"),
    State("conflict-resolution-strategy", "value"),
    State("conflict-rename-input", "value"),
    State("import-data-store", "data"),
    prevent_initial_call=True,
)
def handle_conflict_resolution(
    proceed_clicks, cancel_clicks, strategy, custom_name, import_data
):
    """T052: Handle user's conflict resolution choice with optional custom name."""
    from ui.toast_notifications import create_toast
    from dash import ctx

    if not ctx.triggered or not import_data:
        return no_update, no_update, no_update, no_update, no_update

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if triggered_id == "conflict-cancel":
        return (
            create_toast(
                "Import cancelled by user",
                toast_type="info",
                header="Import Cancelled",
                duration=3000,
            ),
            False,
            no_update,
            no_update,
            None,  # Clear upload contents on cancel too
        )

    # User chose to proceed with selected strategy
    toast, refresh_trigger, profile_switch = perform_import(
        import_data, strategy, custom_name
    )
    return toast, False, refresh_trigger, profile_switch, None  # Clear upload contents


def perform_import(import_data, conflict_strategy=None, custom_name=None):
    """Perform the actual import with optional conflict resolution and custom name."""
    from ui.toast_notifications import create_toast
    from dash import html
    from data.import_export import resolve_profile_conflict
    from data.persistence.factory import get_backend

    try:
        backend = get_backend()

        # Get profile data from new format
        profile_data = import_data.get("profile_data", {})
        profile_id = profile_data.get("id") or import_data.get("profile_id")

        # T026: Detect export mode from manifest
        manifest = import_data.get("manifest", {})
        export_mode = manifest.get("export_mode", "FULL_DATA")
        is_config_only = export_mode == "CONFIG_ONLY"

        # Handle conflict resolution if strategy provided
        if conflict_strategy:
            existing_profile = backend.get_profile(profile_id)
            if existing_profile:
                # If rename strategy and custom name provided, use it
                if (
                    conflict_strategy == "rename"
                    and custom_name
                    and custom_name.strip()
                ):
                    # Validate custom name doesn't already exist
                    import copy

                    final_profile_id = custom_name.strip()

                    # Check if a profile with this name already exists
                    all_profiles = backend.list_profiles()
                    for profile in all_profiles:
                        if profile["name"].lower() == final_profile_id.lower():
                            # Name conflict - return error toast
                            return (
                                create_toast(
                                    [
                                        html.Div(
                                            f"Import failed: Profile with name '{final_profile_id}' already exists."
                                        ),
                                        html.Div(
                                            "Please choose a different name or use the Overwrite option.",
                                            className="mt-2 text-muted",
                                        ),
                                    ],
                                    toast_type="warning",
                                    header="Duplicate Profile Name",
                                    duration=8000,
                                ),
                                no_update,  # No refresh on validation error
                                no_update,  # No profile selector refresh on validation error
                            )

                    # Update profile data with new ID and name (deep copy to avoid mutations)
                    resolved_data = copy.deepcopy(profile_data)
                    resolved_data["id"] = final_profile_id
                    resolved_data["name"] = final_profile_id
                else:
                    # Use default conflict resolution (auto-generate timestamp name)
                    final_profile_id, resolved_data = resolve_profile_conflict(
                        profile_id, conflict_strategy, profile_data, existing_profile
                    )

                profile_id = final_profile_id
                profile_data = resolved_data

        # Ensure required fields are set
        if "created_at" not in profile_data:
            profile_data["created_at"] = datetime.now().isoformat()
        if "last_used" not in profile_data:
            profile_data["last_used"] = datetime.now().isoformat()

        # Save profile to database
        backend.save_profile(profile_data)
        logger.info(f"Imported profile '{profile_id}' to database")

        # Import ALL queries from query_data (full-profile import)
        query_data_dict = import_data.get("query_data", {})
        imported_query_count = 0
        first_imported_query_id = None
        budget_imported = False  # Track if any budget data was imported

        if query_data_dict:
            for exported_query_id, query_data in query_data_dict.items():
                # Get query metadata
                query_metadata = query_data.get("query_metadata", {})
                query_name = query_metadata.get(
                    "name", f"Imported Query {exported_query_id}"
                )
                query_jql = query_metadata.get("jql", "")

                # Generate new query ID (timestamp-based)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                created_query_id = f"q_{timestamp}"

                # Create query record in database
                query_record = {
                    "id": created_query_id,
                    "name": query_name,
                    "jql": query_jql,
                    "created_at": query_metadata.get(
                        "created_at", datetime.now().isoformat()
                    ),
                    "last_used": query_metadata.get(
                        "last_used", datetime.now().isoformat()
                    ),
                }
                backend.save_query(profile_id, query_record)

                # Track first imported query for setting as active
                if first_imported_query_id is None:
                    first_imported_query_id = created_query_id

                # Import FULL_DATA if available
                if export_mode == "FULL_DATA":
                    # Import issues (from jira_cache)
                    if "jira_cache" in query_data:
                        issues = query_data["jira_cache"].get("issues", [])
                        if issues:
                            # Validate issues before import - filter out invalid ones
                            valid_issues = []
                            invalid_count = 0
                            for issue in issues:
                                # Check for required fields (JIRA uses 'key' not 'issue_key')
                                if not issue.get("key"):
                                    invalid_count += 1
                                    logger.warning(
                                        f"Skipping issue without 'key' field in query '{query_name}'"
                                    )
                                    continue

                                # Add required metadata fields
                                if "fetched_at" not in issue:
                                    issue["fetched_at"] = datetime.now().isoformat()
                                if "version" not in issue:
                                    issue["version"] = 1
                                valid_issues.append(issue)

                            # Only import if we have valid issues
                            if valid_issues:
                                # Use cache key from query ID and current timestamp for expiration
                                cache_key = f"import_{created_query_id}"
                                from datetime import timedelta

                                expires_at = datetime.now() + timedelta(days=1)
                                backend.save_issues_batch(
                                    profile_id,
                                    created_query_id,
                                    cache_key,
                                    valid_issues,
                                    expires_at,
                                )
                                logger.info(
                                    f"Imported {len(valid_issues)} valid issues for query '{query_name}'"
                                    + (
                                        f" ({invalid_count} invalid issues skipped)"
                                        if invalid_count > 0
                                        else ""
                                    )
                                )

                    # Import statistics (from statistics)
                    if "statistics" in query_data:
                        statistics = query_data["statistics"]
                        if statistics:
                            backend.save_statistics_batch(
                                profile_id, created_query_id, statistics
                            )
                            logger.info(
                                f"Imported {len(statistics)} statistics for query '{query_name}'"
                            )

                    # Import project scope (Settings Panel parameters)
                    if "project_scope" in query_data:
                        project_scope = query_data["project_scope"]
                        if project_scope:
                            backend.save_scope(
                                profile_id, created_query_id, project_scope
                            )
                            logger.info(
                                f"Imported project scope for query '{query_name}': "
                                f"total_items={project_scope.get('total_items')}, "
                                f"estimated_items={project_scope.get('estimated_items')}, "
                                f"total_points={project_scope.get('remaining_total_points')}, "
                                f"estimated_points={project_scope.get('estimated_points')}"
                            )

                # Import budget data if present in query (query-level budget)
                if "budget_settings" in query_data:
                    budget_settings = query_data["budget_settings"]
                    # Update timestamps for import
                    budget_settings["created_at"] = datetime.now().isoformat()
                    budget_settings["updated_at"] = datetime.now().isoformat()
                    backend.save_budget_settings(
                        profile_id, created_query_id, budget_settings
                    )
                    budget_imported = True  # Mark that budget was imported
                    logger.info(f"Imported budget settings for query '{query_name}'")

                if "budget_revisions" in query_data:
                    budget_revisions = query_data["budget_revisions"]
                    if budget_revisions:
                        backend.save_budget_revisions(
                            profile_id, created_query_id, budget_revisions
                        )
                        logger.info(
                            f"Imported {len(budget_revisions)} budget revisions for query '{query_name}'"
                        )

                imported_query_count += 1
                logger.info(f"Imported query '{query_name}' as {created_query_id}")

            logger.info(
                f"Successfully imported {imported_query_count} queries for profile '{profile_id}'"
            )

        # Set the imported profile as active, and first query as active query
        active_query_id = (
            first_imported_query_id or query_data_dict.keys()[0]
            if query_data_dict
            else None
        )

        if active_query_id:
            backend.set_app_state("active_profile_id", profile_id)
            backend.set_app_state("active_query_id", active_query_id)

        # Budget data is now imported per-query (see query import loop above)
        # Legacy profile-level budget_data in import_data is ignored

        # Log result with strategy info
        strategy_msg = f" ({conflict_strategy} strategy)" if conflict_strategy else ""
        logger.info(
            f"Imported profile {profile_id} with {imported_query_count} queries, active={active_query_id}, mode={export_mode}{strategy_msg}"
        )

        # Check if JIRA token is missing (important for field mappings)
        has_token = bool(profile_data.get("jira_config", {}).get("token", "").strip())

        # T027: Show different message for CONFIG_ONLY imports
        if is_config_only:
            # Build warning message with token guidance
            query_count_msg = (
                f"{imported_query_count} queries"
                if imported_query_count > 1
                else "1 query"
            )
            warning_parts = [
                html.Div(
                    f"Successfully imported profile '{profile_id}' with {query_count_msg}"
                ),
                html.Div(
                    "⚠️ This is a configuration-only import. "
                    "Connect to JIRA and click 'Update Data' to fetch issue data.",
                    className="mt-2 text-warning",
                ),
            ]

            if not has_token:
                warning_parts.append(
                    html.Div(
                        "🔑 JIRA token not included in import. "
                        "Go to Settings → Configure JIRA Connection to add your token. "
                        "Field mappings will be empty until token is configured.",
                        className="mt-2 text-info fw-bold",
                    )
                )

            # Check if budget data was imported
            if budget_imported:
                warning_parts.append(
                    html.Div(
                        "💰 Budget data included in import and has been configured.",
                        className="mt-2 text-success",
                    )
                )
            else:
                warning_parts.append(
                    html.Div(
                        "💰 Budget data not included. Configure in Budget tab if needed.",
                        className="mt-2 text-muted",
                    )
                )

            return (
                create_toast(
                    warning_parts,
                    toast_type="info",
                    header="Config Import Complete",
                    duration=20000,  # Extended duration for important message
                ),
                time.time(),  # Trigger refresh to update profile dropdown
                time.time(),  # Trigger profile selector refresh
            )
        else:
            # Full data import - trigger refresh to reload data

            # Build success message with token guidance if needed
            query_count_msg = (
                f"{imported_query_count} queries"
                if imported_query_count > 1
                else "1 query"
            )
            success_parts = [
                html.Div(
                    f"Successfully imported profile '{profile_id}' with {query_count_msg}"
                ),
                html.Div(
                    "Data loaded successfully. Select a query from the dropdown.",
                    className="mt-2",
                ),
            ]

            if not has_token:
                success_parts.append(
                    html.Div(
                        "🔑 JIRA token not included. Field mappings will be empty until you add your token "
                        "in Settings → Configure JIRA Connection.",
                        className="mt-2 text-warning fw-bold",
                    )
                )

            # Check if budget data was imported
            if budget_imported:
                success_parts.append(
                    html.Div(
                        "💰 Budget data included in import and has been configured.",
                        className="mt-2 text-success",
                    )
                )
            else:
                success_parts.append(
                    html.Div(
                        "💰 Budget data not included. Configure in Budget tab if needed.",
                        className="mt-2 text-muted",
                    )
                )

            return (
                create_toast(
                    success_parts,
                    toast_type="success",
                    header="Import Complete",
                    duration=15000
                    if not has_token
                    else 10000,  # Longer if warning present
                ),
                int(time.time() * 1000),  # Trigger data refresh
                time.time(),  # Trigger profile selector refresh
            )

    except Exception as e:
        logger.error(f"Import failed: {e}", exc_info=True)
        return (
            create_toast(
                [html.Div(f"Import failed: {str(e)}")],
                toast_type="danger",
                header="Import Failed",
                duration=10000,
            ),
            no_update,  # No refresh on error
            no_update,  # No profile selector refresh on error
        )


# ============================================================================
# T013: Token Warning Modal Callbacks
# ============================================================================


@callback(
    Output("token-warning-modal", "is_open"),
    Input("include-token-checkbox", "value"),
    Input("token-warning-proceed", "n_clicks"),
    Input("token-warning-cancel", "n_clicks"),
    prevent_initial_call=True,
)
def show_token_warning_callback(include_token, proceed_clicks, cancel_clicks):
    """Show security warning modal when token inclusion enabled.

    Only show modal when checkbox is clicked by user, not when programmatically set.
    """
    from dash import ctx

    if not ctx.triggered:
        return no_update

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # If checkbox clicked and checked, show modal
    if triggered_id == "include-token-checkbox" and include_token:
        return True

    # If proceed/cancel button clicked, close modal
    if triggered_id in ["token-warning-proceed", "token-warning-cancel"]:
        return False

    return no_update


@callback(
    Output("include-token-checkbox", "value", allow_duplicate=True),
    Input("token-warning-cancel", "n_clicks"),
    prevent_initial_call=True,
)
def cancel_token_warning_callback(cancel_clicks):
    """Handle token warning cancellation - uncheck the checkbox."""
    from dash import ctx

    if not ctx.triggered:
        return no_update

    # User canceled - uncheck the checkbox
    return False


# Clientside callback to show/hide rename input field based on strategy selection
clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="toggleRenameInput"),
    Output("conflict-rename-section", "style"),
    Input("conflict-resolution-strategy", "value"),
)
