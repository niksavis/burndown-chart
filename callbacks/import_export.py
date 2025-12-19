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

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        profile_name = profile_id.replace(" ", "_").replace("/", "_")
        query_name = query_id.replace(" ", "_").replace("/", "_")
        mode_suffix = "config" if export_mode == "CONFIG_ONLY" else "full"
        filename = f"export_{profile_name}_{query_name}_{mode_suffix}_{timestamp}.json"

        # Convert to JSON string
        json_content = json.dumps(export_package, indent=2, ensure_ascii=False)
        file_size_kb = len(json_content) / 1024

        logger.info(
            f"Exported profile/query data: {file_size_kb:.1f} KB, mode={export_mode}, token={include_token}"
        )

        # Return download trigger and success toast
        return (
            {"content": json_content, "filename": filename},
            create_toast(
                "Export Successful",
                f"Profile exported ({file_size_kb:.1f} KB). Mode: {export_mode}",
                "success",
            ),
        )

    except Exception as e:
        logger.error(f"Profile export failed: {e}", exc_info=True)
        return no_update, create_toast(
            "Export Failed", f"Could not export profile: {str(e)}", "danger"
        )


@callback(
    Output("app-notifications", "children", allow_duplicate=True),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    prevent_initial_call=True,
)
def import_profile_data(contents, filename):
    """Import profile and query data from JSON file."""
    from ui.toast_notifications import create_toast
    from dash import html

    if not contents:
        return no_update

    try:
        # Decode uploaded file
        import base64

        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        import_data = json.loads(decoded.decode("utf-8"))

        # Validate structure
        if "profile_id" not in import_data or "query_id" not in import_data:
            return create_toast(
                [html.Div("Invalid import file: missing profile_id or query_id")],
                toast_type="danger",
                header="Import Failed",
                duration=10000,
            )

        profile_id = import_data["profile_id"]
        query_id = import_data["query_id"]

        # Create profile and query directories
        profile_dir = Path("profiles") / profile_id
        query_dir = profile_dir / "queries" / query_id
        query_dir.mkdir(parents=True, exist_ok=True)

        # Write profile.json with updated queries list
        if "profile" in import_data:
            profile_file = profile_dir / "profile.json"
            profile_data_for_file = import_data["profile"].copy()

            # Ensure the imported query is registered in the profile's queries list
            if "queries" not in profile_data_for_file:
                profile_data_for_file["queries"] = []
            if query_id not in profile_data_for_file["queries"]:
                profile_data_for_file["queries"].append(query_id)

            with open(profile_file, "w", encoding="utf-8") as f:
                json.dump(profile_data_for_file, f, indent=2, ensure_ascii=False)

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
        profile_data_for_registry = import_data["profile"].copy()

        # Ensure the imported query is registered in the profile's queries list
        if "queries" not in profile_data_for_registry:
            profile_data_for_registry["queries"] = []
        if query_id not in profile_data_for_registry["queries"]:
            profile_data_for_registry["queries"].append(query_id)

        profiles_registry["profiles"][profile_id] = profile_data_for_registry

        # Set the imported profile and query as active
        profiles_registry["active_profile_id"] = profile_id
        profiles_registry["active_query_id"] = query_id

        # Save updated registry
        with open(profiles_json_path, "w", encoding="utf-8") as f:
            json.dump(profiles_registry, f, indent=2, ensure_ascii=False)

        # Write query data files
        query_data = import_data.get("query_data", {})

        if "project_data" in query_data:
            project_file = query_dir / "project_data.json"
            with open(project_file, "w", encoding="utf-8") as f:
                json.dump(query_data["project_data"], f, indent=2, ensure_ascii=False)

        if "metrics_snapshots" in query_data:
            metrics_file = query_dir / "metrics_snapshots.json"
            with open(metrics_file, "w", encoding="utf-8") as f:
                json.dump(
                    query_data["metrics_snapshots"], f, indent=2, ensure_ascii=False
                )

        logger.info(f"Imported profile {profile_id} / query {query_id}")

        return create_toast(
            [
                html.Div(f"Successfully imported: {profile_id} / {query_id}"),
                html.Div(
                    "Reload the page to see the imported profile.", className="mt-2"
                ),
            ],
            toast_type="success",
            header="Import Complete",
            duration=15000,
        )

    except Exception as e:
        logger.error(f"Import failed: {e}", exc_info=True)
        return create_toast(
            [html.Div(f"Import failed: {str(e)}")],
            toast_type="danger",
            header="Import Failed",
            duration=10000,
        )


# ============================================================================
# T013: Token Warning Modal Callbacks
# ============================================================================


@callback(
    Output("token-warning-modal", "is_open"),
    Input("include-token-checkbox", "value"),
    prevent_initial_call=True,
)
def show_token_warning_callback(include_token):
    """Show security warning modal when token inclusion enabled."""
    return bool(include_token)


@callback(
    Output("include-token-checkbox", "value", allow_duplicate=True),
    Output("token-warning-modal", "is_open", allow_duplicate=True),
    Input("token-warning-proceed", "n_clicks"),
    Input("token-warning-cancel", "n_clicks"),
    prevent_initial_call=True,
)
def confirm_token_warning_callback(proceed_clicks, cancel_clicks):
    """Handle token warning confirmation."""
    from dash import ctx

    if not ctx.triggered:
        return no_update, no_update

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if triggered_id == "token-warning-cancel":
        # User canceled - uncheck the checkbox
        return False, False
    elif triggered_id == "token-warning-proceed":
        # User confirmed - keep checkbox checked
        return True, False

    return no_update, no_update
