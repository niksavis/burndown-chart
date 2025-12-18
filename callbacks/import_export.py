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
    Input("export-profile-button", "n_clicks"),
    prevent_initial_call=True,
)
def export_full_profile(n_clicks):
    """Export profile and query data as single JSON file."""
    if not n_clicks:
        return no_update

    try:
        profile_id = get_active_profile_id()
        query_id = get_active_query_id()

        if not profile_id or not query_id:
            logger.error("No active profile/query for export")
            return no_update

        # Build paths
        profile_dir = Path("profiles") / profile_id
        query_dir = profile_dir / "queries" / query_id

        export_data = {
            "export_version": "1.0",
            "export_timestamp": datetime.now().isoformat(),
            "profile_id": profile_id,
            "query_id": query_id,
        }

        # Load profile.json
        profile_file = Path(profile_dir) / "profile.json"
        if profile_file.exists():
            with open(profile_file, "r", encoding="utf-8") as f:
                export_data["profile"] = json.load(f)

        # Load query data files
        query_data = {}

        # project_data.json
        project_file = Path(query_dir) / "project_data.json"
        if project_file.exists():
            with open(project_file, "r", encoding="utf-8") as f:
                query_data["project_data"] = json.load(f)

        # metrics_snapshots.json
        metrics_file = Path(query_dir) / "metrics_snapshots.json"
        if metrics_file.exists():
            with open(metrics_file, "r", encoding="utf-8") as f:
                query_data["metrics_snapshots"] = json.load(f)

        export_data["query_data"] = query_data  # type: ignore

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        profile_name = profile_id.replace(" ", "_").replace("/", "_")
        query_name = query_id.replace(" ", "_").replace("/", "_")
        filename = f"export_{profile_name}_{query_name}_{timestamp}.json"

        # Convert to JSON string
        json_content = json.dumps(export_data, indent=2, ensure_ascii=False)

        logger.info(f"Exported profile/query data: {len(json_content):,} bytes")

        # Return download trigger
        return {"content": json_content, "filename": filename}

    except Exception as e:
        logger.error(f"Profile export failed: {e}", exc_info=True)
        return no_update


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
