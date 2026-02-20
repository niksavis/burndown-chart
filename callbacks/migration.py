"""Automatic migration callback with user notifications.

Handles automatic migration on app startup with toast notifications
to inform users about the migration progress.
"""

import logging

from dash import Input, Output, State, callback, html, no_update

from data.migration.migration_manager import check_migration_needed, run_migration
from ui.toast_notifications import create_toast

logger = logging.getLogger(__name__)


@callback(
    Output("app-notifications", "children", allow_duplicate=True),
    Output("migration-status", "data"),
    Input("app-init-complete", "data"),
    State("migration-status", "data"),
    prevent_initial_call=True,
)
def handle_automatic_migration(app_init_complete, migration_status):
    """Handle automatic migration on app startup.

    Checks if migration is needed and runs it automatically,
    showing toast notifications to inform the user.

    Args:
        app_init_complete: Signal that app initialization is complete
        migration_status: Current migration status to prevent re-running

    Returns:
        Tuple of (toast_component, new_migration_status)
    """
    # Only run once per session
    if migration_status and migration_status.get("completed"):
        return no_update, no_update

    if not app_init_complete:
        return no_update, no_update

    # Check if migration is needed
    needs_migration, file_counts = check_migration_needed()

    if not needs_migration:
        logger.info("No migration needed - database is up to date")
        return no_update, {"completed": True, "needed": False}

    # Show "migration starting" toast and run migration
    total_files = sum(file_counts.values())
    logger.info(f"Starting automatic migration for {total_files} JSON files")

    # Run migration (this happens in the callback, may take a few seconds)
    success, counts, message = run_migration()

    if success:
        total_migrated = sum(counts.values())
        logger.info(f"Migration complete - migrated {total_migrated:,} items")

        return no_update, {
            "completed": True,
            "needed": True,
            "success": True,
            "counts": counts,
        }
    else:
        # Show error toast only on failure
        error_toast = create_toast(
            [
                html.Div("Migration encountered an error"),
                html.Div(message, className="small text-muted mt-1"),
            ],
            toast_type="danger",
            header="Migration Failed",
            duration=0,  # Don't auto-dismiss errors
            icon="exclamation-triangle",
        )

        return error_toast, {
            "completed": True,
            "needed": True,
            "success": False,
            "error": message,
        }
