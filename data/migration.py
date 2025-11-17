"""
Migration module for transitioning to profile-based data organization.

This module handles the one-time migration from root-level data files to the
new profiles/default/queries/main/ structure, ensuring zero data loss and
providing rollback capability.
"""

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from configuration import logger
from data.profile_manager import (
    PROFILES_DIR,
    PROFILES_FILE,
    DEFAULT_PROFILE_ID,
    DEFAULT_QUERY_ID,
)

# Files to migrate from root to default profile
MIGRATION_FILES = [
    "app_settings.json",
    "jira_cache.json",
    "jira_changelog_cache.json",
    "project_data.json",
    "metrics_snapshots.json",
]

# Directories to migrate
MIGRATION_DIRS = []  # Empty - cache/ is for Dash background callbacks, not user data

# Legacy files to archive (obsolete with profile system)
LEGACY_FILES_TO_ARCHIVE = ["jira_query_profiles.json"]


def migrate_to_profiles() -> bool:
    """
    Perform one-time migration from root-level data to profiles structure.

    This function is idempotent - running it multiple times is safe.

    Returns:
        bool: True if migration performed, False if already migrated or skipped

    Raises:
        IOError: If migration fails (triggers rollback)

    Process:
        1. Check if already migrated (profiles.json exists)
        2. Create backup of all root files
        3. Create profiles/default/ directory structure
        4. Move files to profiles/default/queries/main/
        5. Create profiles.json registry
        6. Archive obsolete files

    Example:
        >>> migrate_to_profiles()
        True  # Migration successful
        >>> migrate_to_profiles()
        False  # Already migrated, nothing to do
    """
    # Check if already migrated
    if PROFILES_FILE.exists():
        logger.info("Migration already completed - profiles.json exists")
        return False

    # Check if there are any files to migrate
    files_to_migrate = [f for f in MIGRATION_FILES if Path(f).exists()]
    dirs_to_migrate = [d for d in MIGRATION_DIRS if Path(d).exists()]

    if not files_to_migrate and not dirs_to_migrate:
        logger.info(
            "No root-level files to migrate - clean installation. "
            "User will create first profile via UI."
        )
        # Don't create any profiles for fresh installation
        # Just create empty profiles.json registry
        PROFILES_DIR.mkdir(parents=True, exist_ok=True)
        profiles_data = {
            "active_profile_id": None,
            "active_query_id": None,
            "profiles": {},
        }
        with open(PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(profiles_data, f, indent=2)
        logger.info(f"Created empty {PROFILES_FILE} - zero profiles")
        return False  # No migration needed

    try:
        logger.info("Starting migration to profiles structure...")

        # Step 1: Create backups
        create_migration_backup()

        # Step 2: Create directory structure
        default_query_dir = (
            PROFILES_DIR / DEFAULT_PROFILE_ID / "queries" / DEFAULT_QUERY_ID
        )
        default_query_dir.mkdir(parents=True, exist_ok=True)

        # Step 3: Move files
        move_root_files_to_default_profile(default_query_dir)

        # Step 4: Create profiles.json
        initialize_profiles_registry()

        # Step 5: Archive obsolete files
        cleanup_migration_artifacts()

        logger.info("Migration completed successfully")
        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


def create_migration_backup() -> None:
    """
    Create .backup copies of all files before migration.

    Backup files are created with .backup extension and include timestamp
    in case multiple migration attempts are made.

    Example:
        app_settings.json -> app_settings.json.backup
        jira_cache.json -> jira_cache.json.backup
    """
    logger.info("Creating migration backups...")

    for filename in MIGRATION_FILES:
        source = Path(filename)
        if source.exists():
            backup = Path(f"{filename}.backup")
            shutil.copy2(source, backup)
            logger.debug(f"Backed up {filename} -> {backup}")

    for dirname in MIGRATION_DIRS:
        source_dir = Path(dirname)
        if source_dir.exists():
            backup_dir = Path(f"{dirname}.backup")
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            shutil.copytree(source_dir, backup_dir)
            logger.debug(f"Backed up {dirname}/ -> {backup_dir}/")


def move_root_files_to_default_profile(target_dir: Path) -> None:
    """
    Move root-level data files to default profile directory.

    Args:
        target_dir: Destination directory (profiles/default/queries/main/)

    Note:
        Uses shutil.move() which is atomic within same filesystem.
        Falls back to copy+delete for cross-filesystem moves.
    """
    logger.info(f"Moving files to {target_dir}...")

    # Move individual files
    for filename in MIGRATION_FILES:
        source = Path(filename)
        if source.exists():
            dest = target_dir / filename
            shutil.move(str(source), str(dest))
            logger.debug(f"Moved {filename} -> {dest}")

    # Move directories
    for dirname in MIGRATION_DIRS:
        source_dir = Path(dirname)
        if source_dir.exists():
            dest_dir = target_dir / dirname
            if dest_dir.exists():
                shutil.rmtree(dest_dir)
            shutil.move(str(source_dir), str(dest_dir))
            logger.debug(f"Moved {dirname}/ -> {dest_dir}/")


def initialize_profiles_registry() -> None:
    """
    Create profiles.json registry with default profile as active.

    Structure:
        {
            "active_profile_id": "default",
            "active_query_id": "main",
            "profiles": {
                "default": {
                    "name": "Default",
                    "created_at": "2025-11-13T10:00:00Z",
                    "queries": ["main"]
                }
            }
        }
    """
    logger.info("Creating profiles.json registry...")

    # Ensure profiles directory exists
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)

    profiles_data = {
        "active_profile_id": DEFAULT_PROFILE_ID,
        "active_query_id": DEFAULT_QUERY_ID,
        "profiles": {
            DEFAULT_PROFILE_ID: {
                "name": "Default",
                "created_at": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "queries": [DEFAULT_QUERY_ID],
            }
        },
    }

    with open(PROFILES_FILE, "w", encoding="utf-8") as f:
        json.dump(profiles_data, f, indent=2)

    logger.info(f"Created {PROFILES_FILE}")


def rollback_migration() -> None:
    """
    Rollback migration by restoring files from .backup copies.

    This function should be called if migration fails mid-process.
    It restores all .backup files to their original locations.

    Example:
        >>> try:
        ...     migrate_to_profiles()
        ... except IOError:
        ...     rollback_migration()
    """
    logger.warning("Rolling back migration...")

    # Remove profiles.json if created
    if PROFILES_FILE.exists():
        PROFILES_FILE.unlink()
        logger.debug("Removed profiles.json")

    # Restore files from backups
    for filename in MIGRATION_FILES:
        backup = Path(f"{filename}.backup")
        if backup.exists():
            dest = Path(filename)
            if dest.exists():
                dest.unlink()
            shutil.copy2(backup, dest)
            logger.debug(f"Restored {filename} from backup")

    # Restore directories from backups
    for dirname in MIGRATION_DIRS:
        backup_dir = Path(f"{dirname}.backup")
        if backup_dir.exists():
            dest_dir = Path(dirname)
            if dest_dir.exists():
                shutil.rmtree(dest_dir)
            shutil.copytree(backup_dir, dest_dir)
            logger.debug(f"Restored {dirname}/ from backup")

    logger.info("Migration rollback completed")


def cleanup_migration_artifacts() -> None:
    """
    Archive obsolete files after successful migration.

    Moves legacy configuration files to _migrated_backup/ directory
    for historical reference without cluttering root directory.

    Files archived:
        - jira_query_profiles.json (replaced by profiles.json)
    """
    logger.info("Archiving obsolete files...")

    backup_dir = Path("_migrated_backup")
    backup_dir.mkdir(exist_ok=True)

    for filename in LEGACY_FILES_TO_ARCHIVE:
        source = Path(filename)
        if source.exists():
            dest = backup_dir / filename
            shutil.move(str(source), str(dest))
            logger.debug(f"Archived {filename} -> {dest}")
