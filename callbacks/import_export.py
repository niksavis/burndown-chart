"""Callbacks for profile import/export functionality."""

from datetime import datetime
import json
import logging
from pathlib import Path
from dash import callback, Output, Input, State, no_update
from data.query_manager import get_active_profile_id, get_active_query_id

logger = logging.getLogger(__name__)

# Note: Report generation callbacks moved to callbacks/report_generation.py


@callback(
    Output("export-profile-download", "data"),
    Output("app-notifications", "children", allow_duplicate=True),
    Input("export-profile-button", "n_clicks"),
    State("export-mode-radio", "value"),
    State("include-token-checkbox", "value"),
    prevent_initial_call=True,
)
def export_full_profile(n_clicks, export_mode, include_token):
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

        # Check if profile already exists
        profile_path = Path("profiles") / profile_id / "profile.json"

        if profile_path.exists():
            # Conflict detected - show modal with profile name
            # Suggest a default name for rename option
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            suggested_name = f"{profile_id}_{timestamp}"
            return True, profile_name, import_data, suggested_name
        else:
            # No conflict - proceed with import directly
            return False, "", import_data, no_update

    except Exception as e:
        logger.error(f"Conflict detection failed: {e}", exc_info=True)
        return False, "", None, no_update


@callback(
    Output("app-notifications", "children", allow_duplicate=True),
    Output("metrics-refresh-trigger", "data", allow_duplicate=True),
    Output("upload-data", "contents", allow_duplicate=True),
    Input("import-data-store", "data"),
    State("conflict-resolution-modal", "is_open"),
    prevent_initial_call=True,
)
def import_without_conflict(import_data, modal_is_open):
    """T051: Handle import when no conflict exists (direct import)."""
    # Only proceed if modal is NOT open (no conflict detected)
    if not import_data or modal_is_open:
        return no_update, no_update, no_update
    toast, refresh = perform_import(import_data)
    return toast, refresh, None  # Clear upload contents


@callback(
    Output("app-notifications", "children", allow_duplicate=True),
    Output("conflict-resolution-modal", "is_open", allow_duplicate=True),
    Output("metrics-refresh-trigger", "data", allow_duplicate=True),
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
    from dash import html, ctx
    from data.import_export import resolve_profile_conflict

    if not ctx.triggered or not import_data:
        return no_update, no_update, no_update, no_update

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
            None,  # Clear upload contents on cancel too
        )

    # User chose to proceed with selected strategy
    toast, refresh_trigger = perform_import(import_data, strategy, custom_name)
    return toast, False, refresh_trigger, None  # Clear upload contents


def perform_import(import_data, conflict_strategy=None, custom_name=None):
    """Perform the actual import with optional conflict resolution and custom name."""
    from ui.toast_notifications import create_toast
    from dash import html
    from data.import_export import resolve_profile_conflict

    try:
        # Get profile data from new format
        profile_data = import_data.get("profile_data", {})
        profile_id = profile_data.get("id") or import_data.get("profile_id")

        # T026: Detect export mode from manifest
        manifest = import_data.get("manifest", {})
        export_mode = manifest.get("export_mode", "FULL_DATA")
        is_config_only = export_mode == "CONFIG_ONLY"

        # Get query info from query_data
        query_data_dict = import_data.get("query_data", {})
        original_query_id = None
        query_metadata = None

        if query_data_dict:
            # Get original query ID
            original_query_id = list(query_data_dict.keys())[0]
            # Get query metadata (name, JQL, description)
            query_metadata = query_data_dict[original_query_id].get(
                "query_metadata", {}
            )

        # Generate new unique query ID (timestamp-based)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        query_id = f"q_{timestamp}"

        # Use friendly query name if available
        query_name = (
            query_metadata.get("name", "Imported Query")
            if query_metadata
            else "Imported Query"
        )
        query_jql = query_metadata.get("jql", "") if query_metadata else ""
        query_description = (
            query_metadata.get("description", "") if query_metadata else ""
        )

        # Handle conflict resolution if strategy provided
        if conflict_strategy:
            profile_path = Path("profiles") / profile_id / "profile.json"
            if profile_path.exists():
                # Load existing profile
                with open(profile_path, "r", encoding="utf-8") as f:
                    existing_profile = json.load(f)

                # If rename strategy and custom name provided, use it
                if (
                    conflict_strategy == "rename"
                    and custom_name
                    and custom_name.strip()
                ):
                    # User provided custom name - use it directly
                    import copy

                    final_profile_id = custom_name.strip()
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

        # Create profile and query directories
        profile_dir = Path("profiles") / profile_id
        query_dir = profile_dir / "queries" / query_id
        query_dir.mkdir(parents=True, exist_ok=True)

        # Write query.json with metadata (name, JQL, description)
        query_file = query_dir / "query.json"
        query_json_data = {
            "name": query_name,
            "jql": query_jql,
            "description": query_description,
            "created_at": datetime.now().isoformat(),
        }
        with open(query_file, "w", encoding="utf-8") as f:
            json.dump(query_json_data, f, indent=2, ensure_ascii=False)

        # Write profile.json
        profile_file = profile_dir / "profile.json"

        # Ensure the imported query is registered in the profile's queries list
        if "queries" not in profile_data:
            profile_data["queries"] = []
        if query_id not in profile_data["queries"]:
            profile_data["queries"].append(query_id)

        with open(profile_file, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False)

        # Update profiles.json registry to register the new profile
        profiles_json_path = Path("profiles") / "profiles.json"
        if profiles_json_path.exists():
            with open(profiles_json_path, "r", encoding="utf-8") as f:
                profiles_registry = json.load(f)
        else:
            profiles_registry = {
                "version": "3.0",
                "active_profile_id": "",
                "active_query_id": "",
                "profiles": {},
            }

        # Add/update profile entry in registry
        profiles_registry["profiles"][profile_id] = profile_data

        # Import ALL queries from query_data (full-profile import)
        query_data_dict = import_data.get("query_data", {})
        imported_query_count = 0
        first_imported_query_id = None

        if query_data_dict:
            for exported_query_id, query_data in query_data_dict.items():
                # Get query metadata
                query_metadata = query_data.get("query_metadata", {})
                query_name = query_metadata.get(
                    "name", f"Imported Query {exported_query_id}"
                )
                query_jql = query_metadata.get("jql", "")

                # Create query using query manager
                from data.query_manager import create_query

                created_query_id = create_query(profile_id, query_name, query_jql)

                # Track first imported query for setting as active
                if first_imported_query_id is None:
                    first_imported_query_id = created_query_id

                # Write query data files for this query
                created_query_dir = profile_dir / "queries" / created_query_id
                created_query_dir.mkdir(parents=True, exist_ok=True)

                if "project_data" in query_data:
                    project_file = created_query_dir / "project_data.json"
                    with open(project_file, "w", encoding="utf-8") as f:
                        json.dump(
                            query_data["project_data"], f, indent=2, ensure_ascii=False
                        )

                if "jira_cache" in query_data:
                    cache_file = created_query_dir / "jira_cache.json"
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(
                            query_data["jira_cache"], f, indent=2, ensure_ascii=False
                        )

                if "metrics_snapshots" in query_data:
                    metrics_file = created_query_dir / "metrics_snapshots.json"
                    with open(metrics_file, "w", encoding="utf-8") as f:
                        json.dump(
                            query_data["metrics_snapshots"],
                            f,
                            indent=2,
                            ensure_ascii=False,
                        )

                imported_query_count += 1
                logger.info(f"Imported query '{query_name}' as {created_query_id}")

            logger.info(
                f"Successfully imported {imported_query_count} queries for profile '{profile_id}'"
            )

        # Set the imported profile as active, and first query as active query
        profiles_registry["active_profile_id"] = profile_id
        profiles_registry["active_query_id"] = first_imported_query_id or query_id

        # Save updated registry
        with open(profiles_json_path, "w", encoding="utf-8") as f:
            json.dump(profiles_registry, f, indent=2, ensure_ascii=False)

        # Log result with strategy info
        strategy_msg = f" ({conflict_strategy} strategy)" if conflict_strategy else ""
        active_query_display = first_imported_query_id or query_id
        logger.info(
            f"Imported profile {profile_id} with {imported_query_count} queries, active={active_query_display}, mode={export_mode}{strategy_msg}"
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

            return (
                create_toast(
                    warning_parts,
                    toast_type="info",
                    header="Config Import Complete",
                    duration=20000,  # Extended duration for important message
                ),
                no_update,  # No refresh for config-only imports
            )
        else:
            # Full data import - trigger refresh to reload data
            import time

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
from dash import clientside_callback, ClientsideFunction

clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="toggleRenameInput"),
    Output("conflict-rename-section", "style"),
    Input("conflict-resolution-strategy", "value"),
)
