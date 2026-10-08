import logging
import shutil
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_PROFILES_PATH = Path("profiles")
DEFAULT_BACKUPS_PATH = Path("backups")


def create_backup(
    profiles_path: Path = DEFAULT_PROFILES_PATH,
    backups_path: Path = DEFAULT_BACKUPS_PATH,
) -> Path:

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = backups_path / f"migration-{timestamp}"

    logger.info(f"Creating backup of {profiles_path} to {backup_dir}")

    if not profiles_path.exists():
        logger.warning(
            f"Profiles directory {profiles_path} does not exist - skipping backup"
        )
        return backup_dir

    if not any(profiles_path.iterdir()):
        logger.warning(f"Profiles directory {profiles_path} is empty - skipping backup")
        return backup_dir

    try:
        backup_dir.mkdir(parents=True, exist_ok=True)

        shutil.copytree(
            profiles_path,
            backup_dir / profiles_path.name,
            dirs_exist_ok=True,
            symlinks=False,
        )

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
        raise OSError(f"Backup creation failed: {e}") from e


def restore_backup(
    backup_path: Path,
    profiles_path: Path = DEFAULT_PROFILES_PATH,
    remove_existing: bool = True,
) -> None:

    logger.info(f"Restoring backup from {backup_path} to {profiles_path}")

    if not backup_path.exists():
        raise ValueError(f"Backup directory {backup_path} does not exist")

    backup_profiles = backup_path / profiles_path.name
    if not backup_profiles.exists():
        raise ValueError(f"Backup does not contain {profiles_path.name} directory")

    try:
        if remove_existing and profiles_path.exists():
            logger.warning(f"Removing existing {profiles_path} directory")
            shutil.rmtree(profiles_path)

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
        raise OSError(f"Backup restore failed: {e}") from e


def list_backups(backups_path: Path = DEFAULT_BACKUPS_PATH) -> list[Path]:

    if not backups_path.exists():
        return []

    backups = [
        p
        for p in backups_path.iterdir()
        if p.is_dir() and p.name.startswith("migration-")
    ]

    backups.sort(reverse=True)

    return backups


def cleanup_old_backups(
    backups_path: Path = DEFAULT_BACKUPS_PATH,
    keep_count: int = 5,
) -> int:

    backups = list_backups(backups_path)

    if len(backups) <= keep_count:
        return 0

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

    if not backup_path.exists():
        return 0

    return sum(f.stat().st_size for f in backup_path.rglob("*") if f.is_file())
