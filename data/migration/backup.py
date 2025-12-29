"""
Backup management for migration safety.

Creates timestamped backups of profiles/ directory before migration.
Provides restore functionality for migration rollback.

Usage:
    from data.migration.backup import create_backup, restore_backup

    # Before migration
    backup_path = create_backup()

    # If migration fails
    restore_backup(backup_path)
"""

import logging
import shutil
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

DEFAULT_PROFILES_PATH = Path("profiles")
DEFAULT_BACKUPS_PATH = Path("backups")


def create_backup(
    profiles_path: Path = DEFAULT_PROFILES_PATH,
    backups_path: Path = DEFAULT_BACKUPS_PATH,
) -> Path:
    """
    Create timestamped backup of profiles directory.

    Copies entire profiles/ directory to backups/migration-{timestamp}/.
    Skips if profiles directory doesn't exist or is empty.

    Args:
        profiles_path: Source profiles directory to backup
        backups_path: Base directory for backups

    Returns:
        Path: Created backup directory path

    Raises:
        IOError: If backup creation fails

    Example:
        >>> from data.migration.backup import create_backup
        >>> backup_path = create_backup()
        >>> print(f"Backup created at {backup_path}")
        Backup created at backups/migration-20251229-143045/
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = backups_path / f"migration-{timestamp}"

    logger.info(f"Creating backup of {profiles_path} to {backup_dir}")

    # Check if source exists
    if not profiles_path.exists():
        logger.warning(
            f"Profiles directory {profiles_path} does not exist - skipping backup"
        )
        return backup_dir

    # Check if source is empty
    if not any(profiles_path.iterdir()):
        logger.warning(f"Profiles directory {profiles_path} is empty - skipping backup")
        return backup_dir

    try:
        # Create backup directory
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Copy entire profiles directory
        shutil.copytree(
            profiles_path,
            backup_dir / profiles_path.name,
            dirs_exist_ok=True,
            symlinks=False,
        )

        # Calculate backup size
        backup_size = sum(
            f.stat().st_size for f in backup_dir.rglob("*") if f.is_file()
        )

        logger.info(
            "Backup created successfully",
            extra={
                "backup_path": str(backup_dir),
                "backup_size_bytes": backup_size,
                "backup_size_mb": f"{backup_size / (1024 * 1024):.2f}",
            },
        )

        return backup_dir

    except Exception as e:
        logger.error(
            f"Failed to create backup: {e}",
            extra={"error_type": type(e).__name__, "profiles_path": str(profiles_path)},
        )
        raise IOError(f"Backup creation failed: {e}") from e


def restore_backup(
    backup_path: Path,
    profiles_path: Path = DEFAULT_PROFILES_PATH,
    remove_existing: bool = True,
) -> None:
    """
    Restore profiles directory from backup.

    Used for migration rollback when migration fails.

    Args:
        backup_path: Path to backup directory to restore from
        profiles_path: Target profiles directory
        remove_existing: If True, remove existing profiles before restore

    Raises:
        IOError: If restore fails
        ValueError: If backup doesn't exist

    Example:
        >>> from data.migration.backup import restore_backup
        >>> restore_backup(Path("backups/migration-20251229-143045"))
    """
    logger.info(f"Restoring backup from {backup_path} to {profiles_path}")

    # Validate backup exists
    if not backup_path.exists():
        raise ValueError(f"Backup directory {backup_path} does not exist")

    backup_profiles = backup_path / profiles_path.name
    if not backup_profiles.exists():
        raise ValueError(f"Backup does not contain {profiles_path.name} directory")

    try:
        # Remove existing profiles if requested
        if remove_existing and profiles_path.exists():
            logger.warning(f"Removing existing {profiles_path} directory")
            shutil.rmtree(profiles_path)

        # Restore from backup
        shutil.copytree(
            backup_profiles,
            profiles_path,
            dirs_exist_ok=True,
            symlinks=False,
        )

        logger.info(f"Backup restored successfully to {profiles_path}")

    except Exception as e:
        logger.error(
            f"Failed to restore backup: {e}",
            extra={"error_type": type(e).__name__, "backup_path": str(backup_path)},
        )
        raise IOError(f"Backup restore failed: {e}") from e


def list_backups(backups_path: Path = DEFAULT_BACKUPS_PATH) -> list[Path]:
    """
    List all migration backups, ordered by timestamp descending.

    Args:
        backups_path: Base directory containing backups

    Returns:
        list[Path]: List of backup directory paths

    Example:
        >>> from data.migration.backup import list_backups
        >>> backups = list_backups()
        >>> for backup in backups:
        ...     print(backup.name)
        migration-20251229-143045
        migration-20251228-091234
    """
    if not backups_path.exists():
        return []

    backups = [
        p
        for p in backups_path.iterdir()
        if p.is_dir() and p.name.startswith("migration-")
    ]

    # Sort by timestamp (newest first)
    backups.sort(reverse=True)

    return backups


def cleanup_old_backups(
    backups_path: Path = DEFAULT_BACKUPS_PATH,
    keep_count: int = 5,
) -> int:
    """
    Remove old migration backups, keeping only the most recent N.

    Args:
        backups_path: Base directory containing backups
        keep_count: Number of most recent backups to keep

    Returns:
        int: Number of backups deleted

    Example:
        >>> from data.migration.backup import cleanup_old_backups
        >>> deleted = cleanup_old_backups(keep_count=3)
        >>> print(f"Deleted {deleted} old backups")
    """
    backups = list_backups(backups_path)

    if len(backups) <= keep_count:
        return 0

    # Delete oldest backups
    to_delete = backups[keep_count:]
    deleted_count = 0

    for backup in to_delete:
        try:
            logger.info(f"Deleting old backup: {backup}")
            shutil.rmtree(backup)
            deleted_count += 1
        except Exception as e:
            logger.error(f"Failed to delete backup {backup}: {e}")

    logger.info(
        f"Cleaned up {deleted_count} old backups (kept {keep_count} most recent)"
    )
    return deleted_count


def get_backup_size(backup_path: Path) -> int:
    """
    Calculate total size of backup directory.

    Args:
        backup_path: Path to backup directory

    Returns:
        int: Total size in bytes

    Example:
        >>> from data.migration.backup import get_backup_size
        >>> size = get_backup_size(Path("backups/migration-20251229-143045"))
        >>> print(f"Backup size: {size / (1024 * 1024):.2f} MB")
    """
    if not backup_path.exists():
        return 0

    return sum(f.stat().st_size for f in backup_path.rglob("*") if f.is_file())
