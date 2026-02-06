"""File operations for updater with retry logic."""

from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import Callable, Optional

StatusFn = Callable[[str], None]


def backup_file(file_path: Path, status: StatusFn) -> Optional[Path]:
    """Create backup of a file.

    Args:
        file_path: Path to file to backup
        status: Callback for status output

    Returns:
        Path to backup file, or None if backup failed
    """
    backup_path = file_path.with_suffix(file_path.suffix + ".bak")

    try:
        status(f"Creating backup: {backup_path.name}")
        shutil.copy2(file_path, backup_path)
        status("Backup created successfully")
        return backup_path
    except Exception as e:
        status(f"ERROR: Failed to create backup: {e}")
        return None


def restore_from_backup(
    backup_path: Path,
    target_path: Path,
    status: StatusFn,
) -> bool:
    """Restore file from backup.

    Args:
        backup_path: Path to backup file
        target_path: Path where to restore the file
        status: Callback for status output

    Returns:
        True if restore succeeded, False otherwise
    """
    max_retries = 20
    retry_delay = 1.0
    start_time = time.time()

    for attempt in range(max_retries):
        try:
            if attempt > 0:
                elapsed = time.time() - start_time
                status(
                    f"Restore retry attempt {attempt + 1}/{max_retries} (elapsed: {elapsed:.1f}s)..."
                )
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 1.5, 5.0)

            status(f"Restoring from backup: {backup_path.name}")

            if target_path.exists():
                target_path.unlink()

            shutil.copy2(backup_path, target_path)
            status("Restore successful")
            return True

        except PermissionError as e:
            if attempt < max_retries - 1:
                elapsed = time.time() - start_time
                status(
                    f"File locked during restore (attempt {attempt + 1}/{max_retries}, elapsed: {elapsed:.1f}s), retrying..."
                )
                continue
            elapsed = time.time() - start_time
            status(
                f"ERROR: Failed to restore from backup after {max_retries} attempts ({elapsed:.1f}s): {e}"
            )
            return False

        except Exception as e:
            status(f"ERROR: Failed to restore from backup: {e}")
            return False

    return False


def replace_executable(
    new_exe_path: Path,
    target_exe_path: Path,
    status: StatusFn,
) -> bool:
    """Replace old executable with new one.

    Args:
        new_exe_path: Path to new executable
        target_exe_path: Path where to place the new executable
        status: Callback for status output

    Returns:
        True if replacement succeeded, False otherwise
    """
    max_retries = 20
    retry_delay = 1.0
    start_time = time.time()

    for attempt in range(max_retries):
        try:
            if attempt > 0:
                elapsed = time.time() - start_time
                status(
                    f"Retry attempt {attempt + 1}/{max_retries} (elapsed: {elapsed:.1f}s)..."
                )
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 1.5, 5.0)

            status(f"Replacing {target_exe_path.name} with new version")

            if not new_exe_path.exists():
                status(f"ERROR: New executable not found: {new_exe_path}")
                return False

            if target_exe_path.exists():
                target_exe_path.unlink()

            shutil.copy2(new_exe_path, target_exe_path)
            status("Replacement successful")
            return True

        except PermissionError as e:
            if attempt < max_retries - 1:
                elapsed = time.time() - start_time
                status(
                    f"File locked (attempt {attempt + 1}/{max_retries}, elapsed: {elapsed:.1f}s), retrying..."
                )
                if attempt == 5:
                    status(
                        "Note: Anti-virus software may be scanning the executable..."
                    )
                    status("This can take 10-30 seconds with admin privileges")
                continue
            elapsed = time.time() - start_time
            status(
                f"ERROR: Failed to replace executable after {max_retries} attempts ({elapsed:.1f}s): {e}"
            )
            status("File may be locked by anti-virus or another process")
            status("TROUBLESHOOTING:")
            status("  1. Check if anti-virus is running a scan")
            status("  2. Add install directory to AV exclusions")
            status("  3. Try update again when AV scan completes")
            return False

        except Exception as e:
            status(f"ERROR: Failed to replace executable: {e}")
            return False

    return False


def copy_executable(
    source_path: Path,
    target_path: Path,
    description: str,
    status: StatusFn,
) -> bool:
    """Copy an executable with retry logic for transient locks.

    Args:
        source_path: Path to the source executable
        target_path: Destination path for the copy
        description: Human-readable description for status logs
        status: Callback for status output

    Returns:
        True if copy succeeded, False otherwise
    """
    max_retries = 10
    retry_delay = 0.5

    for attempt in range(max_retries):
        try:
            if attempt > 0:
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 1.5, 3.0)

            if target_path.exists():
                target_path.unlink()

            shutil.copy2(source_path, target_path)
            status(f"Created {description}: {target_path.name}")
            return True
        except PermissionError:
            if attempt == max_retries - 1:
                status(f"WARNING: Failed to create {description} due to file lock")
                return False
        except Exception as e:
            status(f"WARNING: Failed to create {description}: {e}")
            return False

    return False


def remove_legacy_executable(
    legacy_path: Path,
    description: str,
    status: StatusFn,
) -> bool:
    """Remove a legacy executable with retry logic.

    Args:
        legacy_path: Path to the legacy executable
        description: Human-readable description for status logs
        status: Callback for status output

    Returns:
        True if removal succeeded or file is absent, False otherwise
    """
    if not legacy_path.exists():
        return True

    max_retries = 10
    retry_delay = 0.5

    for attempt in range(max_retries):
        try:
            if attempt > 0:
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 1.5, 3.0)

            legacy_path.unlink()
            status(f"Removed {description}: {legacy_path.name}")
            return True
        except PermissionError:
            if attempt == max_retries - 1:
                status(f"WARNING: Failed to remove {description} due to file lock")
                return False
        except Exception as e:
            status(f"WARNING: Failed to remove {description}: {e}")
            return False

    return False
