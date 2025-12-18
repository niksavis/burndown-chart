"""Callbacks for profile import/export functionality."""

from datetime import datetime
import logging
from dash import callback, Output, Input, State, no_update
from data.import_export import export_profile_enhanced
from data.query_manager import get_active_profile_id

logger = logging.getLogger(__name__)

# Note: Report generation callbacks moved to callbacks/report_generation.py


@callback(
    Output("export-profile-download", "data"),
    Input("export-profile-button", "n_clicks"),
    [
        State("export-type-radio", "value"),
        State("export-options-checklist", "value"),
    ],
    prevent_initial_call=True,
)
def export_full_profile(n_clicks, export_type, options):
    """Export full profile as ZIP file."""
    if not n_clicks:
        return no_update

    try:
        profile_id = get_active_profile_id()
        if not profile_id:
            logger.error("No active profile for export")
            return no_update

        # Map UI options to export parameters
        options = options or []
        include_cache = "cache" in options
        include_queries = "queries" in options
        export_type_param = export_type if export_type == "full" else "quick"

        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        profile_name = profile_id.replace(" ", "_").replace("/", "_")
        filename = f"profile_{profile_name}_{timestamp}.zip"
        export_path = f"profiles/{profile_id}/export_{timestamp}.zip"

        logger.info(
            f"Starting profile export: type={export_type_param}, cache={include_cache}, queries={include_queries}"
        )

        # Call backend export function
        export_profile_enhanced(
            profile_id=profile_id,
            export_path=export_path,
            include_cache=include_cache,
            include_queries=include_queries,
            export_type=export_type_param,
        )

        logger.info(f"Profile export completed: {export_path}")

        # Return download trigger
        return {"path": export_path, "filename": filename}

    except Exception as e:
        logger.error(f"Profile export failed: {e}", exc_info=True)
        return no_update


@callback(
    Output("export-options-collapse", "is_open"),
    Input("export-type-radio", "value"),
)
def toggle_export_options(export_type):
    """Show/hide export options based on export type selection."""
    return export_type == "full"


@callback(
    Output("export-size-estimate", "children"),
    [
        Input("export-options-checklist", "value"),
        Input("export-type-radio", "value"),
    ],
)
def update_export_size_estimate(options, export_type):
    """Calculate estimated export size based on selected options."""
    options = options or []

    # Base sizes
    base_size = 50  # KB (profile.json, manifest)
    metrics_size = 100 if "metrics" in options else 0  # KB
    queries_size = 200 if "queries" in options else 0  # KB
    cache_size = 15000 if "cache" in options else 0  # KB (~15 MB for JIRA cache)

    total_kb = base_size + metrics_size + queries_size + cache_size

    # Format size display
    if total_kb < 1024:
        size_str = f"{total_kb} KB"
    else:
        size_mb = total_kb / 1024
        size_str = f"{size_mb:.1f} MB"

    return f"Estimated size: {size_str}"
