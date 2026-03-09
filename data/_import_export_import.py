"""
Import functions for the import/export system.

T009: Profile import with setup status migration
Team sharing imports
"""

import json
import logging
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from data._import_export_types import ExportManifest
from data.profile_manager import (
    PROFILES_DIR,
    get_profile_file_path,
    load_profiles_metadata,
    save_profiles_metadata,
)
from data.query_manager import create_query

logger = logging.getLogger(__name__)


# ============================================================================
# T009: Profile Import System with Setup Status Migration
# ============================================================================


def import_profile_enhanced(
    import_path: str,
    target_profile_id: str | None = None,
    preserve_setup_status: bool = True,
    validate_dependencies: bool = True,
) -> tuple[bool, str, str | None]:
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

            # Note: Budget data is not in ZIP-based exports
            # Use the callback-based import (perform_import) for budget support
            budget_data = None

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
                profile_data, target_profile_id, temp_path, budget_data
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
    setup_status: dict[str, Any], validate_dependencies: bool
) -> dict[str, Any]:
    """Migrate imported setup status to current system."""
    # Start with imported status
    migrated_status = setup_status.copy()

    # Add import metadata
    migrated_status["import_metadata"] = {
        "imported_at": datetime.now(UTC).isoformat(),
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
                "last_validation": datetime.now(UTC).isoformat(),
            }
        )

    return migrated_status


def _create_profile_from_import(
    profile_data: dict[str, Any],
    profile_id: str,
    import_path: Path,
    budget_data: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    """Create profile from imported data."""
    try:
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
        profile_data["created_at"] = datetime.now(UTC).isoformat()

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

        # Note: Budget data is now per-query (not profile-level)
        # Budget import is handled within query import flow
        # Legacy profile-level budget_data parameter is deprecated

        return True, profile_id

    except Exception as e:
        logger.error(f"Failed to create profile from import: {e}")
        return False, str(e)


def _import_profile_queries(profile_id: str, queries_dir: Path) -> int:
    """Import queries for imported profile."""
    try:
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
# T009: Team Sharing Import
# ============================================================================


def import_shared_profile(
    import_path: str, team_member_name: str
) -> tuple[bool, str, str | None]:
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
