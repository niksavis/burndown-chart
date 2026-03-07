"""
Data classes and helper types for the import/export system.

T009: ExportManifest and SetupStatusMigrator
T013: Enhanced export mode fields
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

# ============================================================================
# T009: Data Classes and Types
# ============================================================================


@dataclass
class ExportManifest:
    """Metadata for exported profiles."""

    version: str
    created_at: str
    created_by: str
    export_type: str  # "backup", "sharing", "migration"
    profiles: list[str]
    includes_cache: bool
    includes_queries: bool
    includes_setup_status: bool
    # T013: Enhanced Import/Export Options
    export_mode: str = "FULL_DATA"  # "CONFIG_ONLY" | "FULL_DATA"
    includes_token: bool = False  # Whether JIRA token is included
    includes_changelog: bool = False  # Whether changelog entries are included


class SetupStatusMigrator:
    """Handles migration of setup status between profile versions."""

    @staticmethod
    def migrate_status_v2_to_v3(old_status: dict[str, Any]) -> dict[str, Any]:
        """Migrate setup status from v2 to v3 format."""
        # V3 adds dependency tracking and validation history
        migrated = old_status.copy()

        # Add new v3 fields with safe defaults
        migrated.update(
            {
                "dependency_tracking": {
                    "jira_validated_at": old_status.get("jira_connected_at"),
                    "fields_validated_at": old_status.get("fields_mapped_at"),
                    "validation_history": [],
                },
                "migration_metadata": {
                    "migrated_from_version": "2.0",
                    "migrated_at": datetime.now(UTC).isoformat(),
                    "migration_notes": "Auto-migrated from v2 setup status",
                },
            }
        )

        return migrated

    @staticmethod
    def preserve_user_progress(
        imported_status: dict[str, Any], validate_on_import: bool = True
    ) -> dict[str, Any]:
        """Preserve user setup progress while ensuring data integrity."""
        preserved = imported_status.copy()

        if validate_on_import:
            # Mark for re-validation but preserve completed steps
            preserved.update(
                {
                    "validation_pending": True,
                    "validation_required_reason": "Imported from external source",
                    "imported_progress": {
                        "original_setup_complete": imported_status.get(
                            "setup_complete", False
                        ),
                        "original_current_step": imported_status.get("current_step"),
                        "steps_to_revalidate": ["jira_connection", "field_mapping"],
                    },
                }
            )

        return preserved
