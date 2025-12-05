"""
T009: Enhanced Import/Export System with Setup Status Migration

Provides comprehensive profile import/export capabilities with:
- Setup status preservation and migration
- Team sharing workflows
- Full system backup and restore
- Data validation and dependency checking
"""

import json
import logging
import tempfile
import zipfile
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)


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
    profiles: List[str]
    includes_cache: bool
    includes_queries: bool
    includes_setup_status: bool


class SetupStatusMigrator:
    """Handles migration of setup status between profile versions."""

    @staticmethod
    def migrate_status_v2_to_v3(old_status: Dict[str, Any]) -> Dict[str, Any]:
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
                    "migrated_at": datetime.now(timezone.utc).isoformat(),
                    "migration_notes": "Auto-migrated from v2 setup status",
                },
            }
        )

        return migrated

    @staticmethod
    def preserve_user_progress(
        imported_status: Dict[str, Any], validate_on_import: bool = True
    ) -> Dict[str, Any]:
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


# ============================================================================
# T009: Profile Export System with Setup Status Migration
# ============================================================================


def export_profile_enhanced(
    profile_id: str,
    export_path: str,
    include_cache: bool = False,
    include_queries: bool = True,
    export_type: str = "backup",
) -> Tuple[bool, str]:
    """Export profile with T009 setup status migration capabilities.

    Args:
        profile_id: Profile ID to export
        export_path: Output file path
        include_cache: Whether to include cached JIRA data
        include_queries: Whether to include saved queries
        export_type: Type of export (backup/sharing/migration)

    Returns:
        Tuple of (success, message)
    """
    try:
        # Load profile data
        from data.profile_manager import get_profile, get_profile_file_path

        profile_path = get_profile_file_path(profile_id)
        if not profile_path.exists():
            return False, f"Profile '{profile_id}' not found"

        profile_data = get_profile(profile_id)
        if not profile_data:
            return False, f"Failed to load profile '{profile_id}'"

        # Create temporary directory for export
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Prepare profile data for export
            export_data = _prepare_profile_for_export(profile_data, export_type)

            # Create export manifest
            manifest = ExportManifest(
                version="1.0",
                created_at=datetime.now(timezone.utc).isoformat(),
                created_by=f"burndown-chart-{export_type}",
                export_type=export_type,
                profiles=[profile_id],
                includes_cache=include_cache,
                includes_queries=include_queries,
                includes_setup_status=True,
            )

            # Write files to temp directory
            with open(temp_path / "manifest.json", "w") as f:
                json.dump(asdict(manifest), f, indent=2)

            with open(temp_path / "profile.json", "w") as f:
                json.dump(export_data, f, indent=2)

            # Export queries if requested
            queries_exported = 0
            if include_queries:
                queries_exported = _export_profile_queries(profile_id, temp_path)

            # Export cache if requested
            cache_exported = False
            if include_cache:
                cache_exported = _export_profile_cache(profile_id, temp_path)

            # Create ZIP file
            with zipfile.ZipFile(export_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for file_path in temp_path.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(temp_path)
                        zip_file.write(file_path, arcname)

        # Build success message
        components = [f"profile '{profile_id}'"]
        if queries_exported > 0:
            components.append(f"{queries_exported} queries")
        if cache_exported:
            components.append("cached data")

        message = f"Exported {', '.join(components)} to {export_path}"
        logger.info(message)

        return True, message

    except Exception as e:
        logger.error(f"Failed to export profile '{profile_id}': {e}")
        return False, f"Export failed: {e}"


def _prepare_profile_for_export(
    profile_data: Dict[str, Any], export_type: str
) -> Dict[str, Any]:
    """Prepare profile data for export with setup status handling."""
    # Deep copy to avoid modifying original
    profile_data = json.loads(json.dumps(profile_data))

    # Enhance setup status for export
    if "setup_status" not in profile_data:
        # Create minimal setup status for legacy profiles
        profile_data["setup_status"] = {
            "setup_complete": False,
            "current_step": "jira_connection",
            "export_metadata": {
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "source_version": "3.0",
                "was_legacy_profile": True,
            },
        }
    else:
        # Add export metadata to existing setup status
        profile_data["setup_status"]["export_metadata"] = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "source_version": "3.0",
            "original_setup_complete": profile_data["setup_status"].get(
                "setup_complete", False
            ),
        }

    # Clean sensitive data
    if "jira_config" in profile_data:
        # Remove sensitive fields but keep structure
        jira_config = profile_data["jira_config"].copy()
        if "token" in jira_config:
            jira_config["token"] = "<REDACTED_FOR_EXPORT>"
        profile_data["jira_config"] = jira_config

    return profile_data


def _export_profile_queries(profile_id: str, export_dir: Path) -> int:
    """Export all queries for a profile."""
    try:
        from data.query_manager import list_queries_for_profile

        queries = list_queries_for_profile(profile_id)
        queries_dir = export_dir / "queries"
        queries_dir.mkdir()

        for query in queries:
            query_file = queries_dir / f"{query['id']}.json"
            with open(query_file, "w") as f:
                json.dump(query, f, indent=2)

        return len(queries)

    except Exception as e:
        logger.warning(f"Failed to export queries: {e}")
        return 0


def _export_profile_cache(profile_id: str, export_dir: Path) -> bool:
    """Export cached data for a profile."""
    try:
        from data.profile_manager import PROFILES_DIR

        profile_dir = PROFILES_DIR / profile_id
        cache_files = [
            "app_settings.json",
            "project_data.json",
            "jira_cache.json",
            "jira_changelog_cache.json",
            "metrics_snapshots.json",
        ]

        cache_dir = export_dir / "cache"
        cache_dir.mkdir()

        exported = False
        for cache_file in cache_files:
            source = profile_dir / cache_file
            if source.exists():
                dest = cache_dir / cache_file
                dest.write_text(source.read_text())
                exported = True

        return exported

    except Exception as e:
        logger.warning(f"Failed to export cache: {e}")
        return False


# ============================================================================
# T009: Profile Import System with Setup Status Migration
# ============================================================================


def import_profile_enhanced(
    import_path: str,
    target_profile_id: Optional[str] = None,
    preserve_setup_status: bool = True,
    validate_dependencies: bool = True,
) -> Tuple[bool, str, Optional[str]]:
    """Import profile with T009 setup status migration and validation.

    Args:
        import_path: Path to export ZIP file
        target_profile_id: New profile ID (generated if None)
        preserve_setup_status: Whether to preserve exported setup status
        validate_dependencies: Whether to validate setup dependencies

    Returns:
        Tuple of (success, message, new_profile_id)
    """
    try:
        # Extract and validate import package
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Extract ZIP
            with zipfile.ZipFile(import_path, "r") as zip_file:
                zip_file.extractall(temp_path)

            # Load and validate manifest
            manifest_file = temp_path / "manifest.json"
            if not manifest_file.exists():
                return False, "Invalid export file - missing manifest", None

            with open(manifest_file) as f:
                manifest_data = json.load(f)
                # Validate manifest structure
                _ = ExportManifest(**manifest_data)

            # Load profile data
            profile_file = temp_path / "profile.json"
            if not profile_file.exists():
                return False, "Invalid export file - missing profile data", None

            with open(profile_file) as f:
                profile_data = json.load(f)

            # Generate target profile ID if not provided
            if not target_profile_id:
                base_name = profile_data.get("name", "Imported Profile")
                target_profile_id = _generate_unique_profile_id(base_name)

            # Migrate setup status if needed
            setup_status = profile_data.get("setup_status", {})
            if preserve_setup_status and setup_status:
                migrated_status = _migrate_imported_setup_status(
                    setup_status, validate_dependencies
                )
                profile_data["setup_status"] = migrated_status

            # Create profile
            success, new_profile_id = _create_profile_from_import(
                profile_data, target_profile_id, temp_path
            )

            if not success:
                return False, f"Failed to create profile: {new_profile_id}", None

            logger.info(f"Successfully imported profile as '{new_profile_id}'")
            return (
                True,
                f"Profile imported successfully as '{new_profile_id}'",
                new_profile_id,
            )

    except Exception as e:
        logger.error(f"Failed to import profile: {e}")
        return False, f"Import failed: {e}", None


def _generate_unique_profile_id(base_name: str) -> str:
    """Generate unique profile ID for import."""
    from data.profile_manager import get_profile_file_path

    # Create base ID from name
    base_id = base_name.lower().replace(" ", "-")
    base_id = "".join(c for c in base_id if c.isalnum() or c == "-")
    base_id = base_id.strip("-") or "imported-profile"

    # Find unique ID
    if not get_profile_file_path(base_id).exists():
        return base_id

    counter = 2
    while get_profile_file_path(f"{base_id}-{counter}").exists():
        counter += 1

    return f"{base_id}-{counter}"


def _migrate_imported_setup_status(
    setup_status: Dict[str, Any], validate_dependencies: bool
) -> Dict[str, Any]:
    """Migrate imported setup status to current system."""
    # Start with imported status
    migrated_status = setup_status.copy()

    # Add import metadata
    migrated_status["import_metadata"] = {
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "original_exported_at": setup_status.get("export_metadata", {}).get(
            "exported_at"
        ),
        "migration_applied": True,
        "validation_pending": validate_dependencies,
    }

    # Reset status if validation is required
    if validate_dependencies:
        # Keep the structure but mark for re-validation
        migrated_status.update(
            {
                "jira_connected": False,  # Must re-verify connection
                "fields_mapped": False,  # Must re-verify field mappings
                "setup_complete": False,
                "current_step": "jira_connection",
                "last_validation": datetime.now(timezone.utc).isoformat(),
            }
        )

    return migrated_status


def _create_profile_from_import(
    profile_data: Dict[str, Any], profile_id: str, import_path: Path
) -> Tuple[bool, str]:
    """Create profile from imported data."""
    try:
        from data.profile_manager import (
            get_profile_file_path,
            PROFILES_DIR,
            load_profiles_metadata,
            save_profiles_metadata,
        )

        # Extract profile name for creation
        profile_name = profile_data.get("name", f"Imported Profile {profile_id}")

        # Create profile directory manually since we need to preserve all imported data
        profile_dir = PROFILES_DIR / profile_id
        queries_dir = profile_dir / "queries"
        profile_dir.mkdir(parents=True, exist_ok=True)
        queries_dir.mkdir(exist_ok=True)

        # Update profile data with new ID and timestamp
        profile_data["id"] = profile_id
        profile_data["name"] = profile_name
        profile_data["created_at"] = datetime.now(timezone.utc).isoformat()

        # Remove sensitive data that needs re-entry
        if "jira_config" in profile_data:
            jira_config = profile_data["jira_config"]
            if jira_config.get("token") == "<REDACTED_FOR_EXPORT>":
                jira_config["token"] = ""  # Clear redacted token

        # Write profile.json with all imported data
        profile_path = get_profile_file_path(profile_id)
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=2)

        # Register profile in metadata
        metadata = load_profiles_metadata()
        if "profiles" not in metadata:
            metadata["profiles"] = {}
        metadata["profiles"][profile_id] = profile_data
        save_profiles_metadata(metadata)

        # Import queries if available
        queries_dir = import_path / "queries"
        if queries_dir.exists():
            _import_profile_queries(profile_id, queries_dir)

        # Import cache if available and requested
        cache_dir = import_path / "cache"
        if cache_dir.exists():
            _import_profile_cache(profile_id, cache_dir)

        return True, profile_id

    except Exception as e:
        logger.error(f"Failed to create profile from import: {e}")
        return False, str(e)


def _import_profile_queries(profile_id: str, queries_dir: Path) -> int:
    """Import queries for imported profile."""
    try:
        from data.query_manager import create_query

        imported = 0
        for query_file in queries_dir.glob("*.json"):
            with open(query_file) as f:
                query_data = json.load(f)

            # Create query (imported data should be trusted)
            create_query(
                profile_id,
                query_data["name"],
                query_data["jql"],
            )
            imported += 1

        logger.info(f"Imported {imported} queries for profile '{profile_id}'")
        return imported

    except Exception as e:
        logger.warning(f"Failed to import queries: {e}")
        return 0


def _import_profile_cache(profile_id: str, cache_dir: Path) -> bool:
    """Import cached data for imported profile."""
    try:
        from data.profile_manager import PROFILES_DIR

        target_dir = PROFILES_DIR / profile_id
        target_dir.mkdir(parents=True, exist_ok=True)

        imported = False
        for cache_file in cache_dir.glob("*.json"):
            target_file = target_dir / cache_file.name
            target_file.write_text(cache_file.read_text())
            imported = True

        return imported

    except Exception as e:
        logger.warning(f"Failed to import cache: {e}")
        return False


# ============================================================================
# T009: Team Sharing Workflows
# ============================================================================


def export_for_team_sharing(
    profile_id: str,
    export_path: str,
    share_level: str = "configuration",  # "configuration", "with_queries", "full"
) -> Tuple[bool, str]:
    """Export profile for team sharing with appropriate data filtering.

    Args:
        profile_id: Profile to export
        export_path: Export file path
        share_level: Level of data sharing (configuration/with_queries/full)

    Returns:
        Tuple of (success, message)
    """
    include_cache = share_level == "full"
    include_queries = share_level in ["with_queries", "full"]

    return export_profile_enhanced(
        profile_id,
        export_path,
        include_cache=include_cache,
        include_queries=include_queries,
        export_type="team_sharing",
    )


def import_shared_profile(
    import_path: str, team_member_name: str
) -> Tuple[bool, str, Optional[str]]:
    """Import shared profile with team-specific adaptations.

    Args:
        import_path: Path to shared export file
        team_member_name: Name of team member importing

    Returns:
        Tuple of (success, message, new_profile_id)
    """
    # Generate team-specific profile ID
    timestamp = datetime.now().strftime("%Y%m%d")
    target_profile_id = f"shared-{team_member_name.lower()}-{timestamp}"

    # Import with validation required (team members need to configure their own JIRA)
    return import_profile_enhanced(
        import_path,
        target_profile_id=target_profile_id,
        preserve_setup_status=False,  # Reset status for new team member
        validate_dependencies=True,  # Require full setup validation
    )


# ============================================================================
# T009: Migration and Backup Utilities
# ============================================================================


def create_full_system_backup(backup_path: str) -> Tuple[bool, str]:
    """Create complete system backup including all profiles and setup state.

    Args:
        backup_path: Path for backup file

    Returns:
        Tuple of (success, message)
    """
    try:
        from data.profile_manager import list_profiles

        profiles = list_profiles()
        if not profiles:
            return False, "No profiles found to backup"

        # Create temporary directory for full backup
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            backup_dir = temp_path / "system_backup"
            backup_dir.mkdir()

            # Create system manifest
            manifest = ExportManifest(
                version="1.0",
                created_at=datetime.now(timezone.utc).isoformat(),
                created_by="burndown-chart-backup",
                export_type="full_system",
                profiles=[p["id"] for p in profiles],
                includes_cache=True,
                includes_queries=True,
                includes_setup_status=True,
            )

            with open(backup_dir / "system_manifest.json", "w") as f:
                json.dump(asdict(manifest), f, indent=2)

            # Backup each profile
            profiles_dir = backup_dir / "profiles"
            profiles_dir.mkdir()

            for profile in profiles:
                profile_id = profile["id"]
                profile_backup_file = profiles_dir / f"{profile_id}.zip"

                success, message = export_profile_enhanced(
                    profile_id,
                    str(profile_backup_file),
                    include_cache=True,
                    include_queries=True,
                    export_type="backup",
                )

                if not success:
                    logger.warning(
                        f"Failed to backup profile '{profile_id}': {message}"
                    )

            # Create final backup archive
            with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for file_path in backup_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(backup_dir)
                        zip_file.write(file_path, arcname)

        logger.info(f"System backup created: {backup_path}")
        return True, f"Full system backup created with {len(profiles)} profiles"

    except Exception as e:
        logger.error(f"System backup failed: {e}")
        return False, f"Backup failed: {e}"


def restore_from_system_backup(
    backup_path: str,
    restore_mode: str = "merge",  # "merge", "replace", "selective"
) -> Tuple[bool, str]:
    """Restore system from full backup with setup status preservation.

    Args:
        backup_path: Path to system backup file
        restore_mode: How to handle existing profiles

    Returns:
        Tuple of (success, message)
    """
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Extract system backup
            with zipfile.ZipFile(backup_path, "r") as zip_file:
                zip_file.extractall(temp_path)

            # Load system manifest
            manifest_file = temp_path / "system_manifest.json"
            if not manifest_file.exists():
                return False, "Invalid backup file - missing system manifest"

            with open(manifest_file) as f:
                manifest_data = json.load(f)
                # Validate system manifest structure
                _ = ExportManifest(**manifest_data)

            # Restore profiles
            profiles_dir = temp_path / "profiles"
            if not profiles_dir.exists():
                return False, "Invalid backup file - missing profiles"

            restored_profiles = []
            for profile_backup in profiles_dir.glob("*.zip"):
                success, message, profile_id = import_profile_enhanced(
                    str(profile_backup),
                    preserve_setup_status=True,
                    validate_dependencies=False,  # Trust backup data
                )

                if success and profile_id:
                    restored_profiles.append(profile_id)
                else:
                    logger.warning(
                        f"Failed to restore profile {profile_backup.stem}: {message}"
                    )

            return (
                True,
                f"Restored {len(restored_profiles)} profiles: {', '.join(restored_profiles)}",
            )

    except Exception as e:
        logger.error(f"System restore failed: {e}")
        return False, f"Restore failed: {e}"
