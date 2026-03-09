"""
System backup and restore for the import/export system.

T009: Full system backup with all profiles and setup state
"""

import json
import logging
import tempfile
import zipfile
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from data._import_export_export import export_profile_enhanced
from data._import_export_import import import_profile_enhanced
from data._import_export_types import ExportManifest
from data.profile_manager import list_profiles

logger = logging.getLogger(__name__)


def create_full_system_backup(backup_path: str) -> tuple[bool, str]:
    """Create complete system backup including all profiles and setup state.

    Args:
        backup_path: Path for backup file

    Returns:
        Tuple of (success, message)
    """
    try:
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
                created_at=datetime.now(UTC).isoformat(),
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
) -> tuple[bool, str]:
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
                f"Restored {len(restored_profiles)} profiles: "
                f"{', '.join(restored_profiles)}",
            )

    except Exception as e:
        logger.error(f"System restore failed: {e}")
        return False, f"Restore failed: {e}"
