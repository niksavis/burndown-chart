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
    Output("import-status-alert", "children"),
    Output("import-status-alert", "color"),
    Output("import-status-alert", "is_open"),
    Input("import-upload", "contents"),
    State("import-upload", "filename"),
    prevent_initial_call=True,
)
def import_profile_data(contents, filename):
    """Import profile and query data from JSON file."""
    if not contents:
        return no_update, no_update, no_update

    try:
        # Decode uploaded file
        import base64

        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        import_data = json.loads(decoded.decode("utf-8"))

        # Validate structure
        if "profile_id" not in import_data or "query_id" not in import_data:
            return "Invalid import file: missing profile_id or query_id", "danger", True

        profile_id = import_data["profile_id"]
        query_id = import_data["query_id"]

        # Create profile and query directories
        profile_dir = Path("profiles") / profile_id
        query_dir = profile_dir / "queries" / query_id
        query_dir.mkdir(parents=True, exist_ok=True)

        # Write profile.json
        if "profile" in import_data:
            profile_file = profile_dir / "profile.json"
            with open(profile_file, "w", encoding="utf-8") as f:
                json.dump(import_data["profile"], f, indent=2, ensure_ascii=False)

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

        return (
            f"Successfully imported: {profile_id} / {query_id}. Reload the page to see the imported data.",
            "success",
            True,
        )

    except Exception as e:
        logger.error(f"Import failed: {e}", exc_info=True)
        return f"Import failed: {str(e)}", "danger", True
