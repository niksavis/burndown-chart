"""
Enhanced Import/Export System.

T009: Setup status preservation and migration
T013: Multiple export modes, credential control, conflict resolution

Public API re-exported from focused sub-modules:
- _import_export_types:      ExportManifest, SetupStatusMigrator
- _import_export_validation: strip_credentials, validate_import_data,
                             resolve_profile_conflict
- _import_export_export:     export_profile_enhanced, export_profile_with_mode,
                             export_for_team_sharing
- _import_export_import:     import_profile_enhanced, import_shared_profile
- _import_export_backup:     create_full_system_backup, restore_from_system_backup
"""

from data._import_export_backup import (
    create_full_system_backup,
    restore_from_system_backup,
)
from data._import_export_export import (
    export_for_team_sharing,
    export_profile_enhanced,
    export_profile_with_mode,
)
from data._import_export_import import (
    import_profile_enhanced,
    import_shared_profile,
)
from data._import_export_types import ExportManifest, SetupStatusMigrator
from data._import_export_validation import (
    resolve_profile_conflict,
    strip_credentials,
    validate_import_data,
)

__all__ = [
    "ExportManifest",
    "SetupStatusMigrator",
    "strip_credentials",
    "validate_import_data",
    "resolve_profile_conflict",
    "export_profile_enhanced",
    "export_profile_with_mode",
    "export_for_team_sharing",
    "import_profile_enhanced",
    "import_shared_profile",
    "create_full_system_backup",
    "restore_from_system_backup",
]
