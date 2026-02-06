"""
Burndown Updater

Standalone updater executable that replaces the main application with a new version.
This runs as a separate process after the main app exits.

Usage (Original - app only):
    BurndownUpdater.exe <current_exe> <update_zip> <app_pid>

Usage (New - app + updater):
    BurndownUpdater.exe <current_exe> <update_zip> <app_pid> --updater-exe <updater_exe>

Arguments:
    current_exe: Path to the current Burndown.exe to be replaced
    update_zip: Path to the ZIP file containing the new version
    app_pid: Process ID of the running app (to wait for exit)
    --updater-exe: (Optional) Path to current updater executable to be replaced

Flow:
    1. Wait for app.exe to exit (or timeout after 10 seconds)
    2. Backup current exe to .bak file
    3. Extract new version from ZIP
    4. Replace old app exe with new app exe
    5. If --updater-exe provided, replace old updater exe with new updater exe
    6. Restart the application
    7. Clean up temporary files

Error Handling:
    - If backup fails, abort update
    - If extraction fails, restore from backup
    - If replacement fails, restore from backup
    - If relaunch fails, leave new version in place

Exit Codes:
    0: Update successful
    1: Invalid arguments
    2: App didn't exit in time
    3: Backup failed
    4: Extraction failed
    5: Replacement failed
    6: Unknown error
"""

import os
import sys
import tempfile
import time
import zipfile
import shutil
import subprocess
import sqlite3
from pathlib import Path
from typing import Optional

APP_NAME = "Burndown"
MAIN_EXE_NAME = "Burndown.exe"
LEGACY_MAIN_EXE_NAME = "BurndownChart.exe"
UPDATER_EXE_NAME = "BurndownUpdater.exe"
LEGACY_UPDATER_EXE_NAME = "BurndownChartUpdater.exe"


def print_status(message: str) -> None:
    """Print status message to console.

    Args:
        message: Status message to display
    """
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


def wait_for_process_exit(pid: int, timeout: int = 10) -> bool:
    """Wait for a process to exit.

    Args:
        pid: Process ID to wait for
        timeout: Maximum time to wait in seconds

    Returns:
        True if process exited, False if timeout
    """
    print_status(f"Waiting for process {pid} to exit (timeout: {timeout}s)...")

    # Try psutil for faster process detection
    try:
        import psutil

        start_time = time.time()
        while time.time() - start_time < timeout:
            if not psutil.pid_exists(pid):
                print_status(f"Process {pid} has exited")
                return True
            time.sleep(0.1)  # Fast polling with psutil
    except ImportError:
        # Fallback to platform-specific methods
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # On Windows, check if process exists
                if sys.platform == "win32":
                    # Use tasklist to check if process exists
                    result = subprocess.run(
                        ["tasklist", "/FI", f"PID eq {pid}"],
                        capture_output=True,
                        text=True,
                        timeout=1,
                    )
                    # If PID not found in output, process has exited
                    if str(pid) not in result.stdout:
                        print_status(f"Process {pid} has exited")
                        return True
                else:
                    # On Unix, try to send signal 0 (doesn't kill, just checks existence)
                    os.kill(pid, 0)

                # Process still running, wait a bit
                time.sleep(0.2)  # Reduced from 0.5s

            except (ProcessLookupError, OSError):
                # Process doesn't exist anymore
                print_status(f"Process {pid} has exited")
                return True
            except Exception as e:
                print_status(f"Warning: Error checking process status: {e}")
                # Continue waiting
                time.sleep(0.2)

    print_status(f"Timeout waiting for process {pid} to exit")
    return False


def backup_file(file_path: Path) -> Optional[Path]:
    """Create backup of a file.

    Args:
        file_path: Path to file to backup

    Returns:
        Path to backup file, or None if backup failed
    """
    backup_path = file_path.with_suffix(file_path.suffix + ".bak")

    try:
        print_status(f"Creating backup: {backup_path.name}")
        shutil.copy2(file_path, backup_path)
        print_status("Backup created successfully")
        return backup_path
    except Exception as e:
        print_status(f"ERROR: Failed to create backup: {e}")
        return None


def restore_from_backup(backup_path: Path, target_path: Path) -> bool:
    """Restore file from backup.

    Args:
        backup_path: Path to backup file
        target_path: Path where to restore the file

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
                print_status(
                    f"Restore retry attempt {attempt + 1}/{max_retries} (elapsed: {elapsed:.1f}s)..."
                )
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 1.5, 5.0)

            print_status(f"Restoring from backup: {backup_path.name}")

            # Remove corrupted file if it exists
            if target_path.exists():
                target_path.unlink()

            # Restore from backup
            shutil.copy2(backup_path, target_path)
            print_status("Restore successful")
            return True

        except PermissionError as e:
            if attempt < max_retries - 1:
                elapsed = time.time() - start_time
                print_status(
                    f"File locked during restore (attempt {attempt + 1}/{max_retries}, elapsed: {elapsed:.1f}s), retrying..."
                )
                continue
            else:
                elapsed = time.time() - start_time
                print_status(
                    f"ERROR: Failed to restore from backup after {max_retries} attempts ({elapsed:.1f}s): {e}"
                )
                return False

        except Exception as e:
            print_status(f"ERROR: Failed to restore from backup: {e}")
            return False

    return False


def extract_update(zip_path: Path, extract_dir: Path) -> bool:
    """Extract update ZIP to directory.

    Args:
        zip_path: Path to ZIP file
        extract_dir: Directory where to extract files

    Returns:
        True if extraction succeeded, False otherwise
    """
    try:
        print_status(f"Extracting update from {zip_path.name}")

        # Note: extract_dir uses unique UUID name, so conflicts are extremely unlikely
        # But defensive: clean if somehow exists (e.g., UUID collision, though astronomically rare)
        if extract_dir.exists():
            print_status(
                f"WARNING: Extraction directory already exists (UUID collision?): {extract_dir}"
            )
            try:
                shutil.rmtree(extract_dir)
                print_status("Removed existing directory")
            except Exception as e:
                print_status(f"ERROR: Failed to remove existing directory: {e}")
                return False  # Fail fast if we can't clean

        # Create extraction directory
        try:
            extract_dir.mkdir(parents=True, exist_ok=True)
            print_status(f"Created extraction directory: {extract_dir}")
        except PermissionError as e:
            print_status(f"ERROR: Permission denied creating directory: {extract_dir}")
            print_status(f"Details: {e}")
            return False
        except Exception as e:
            print_status(f"ERROR: Could not create temporary directory: {extract_dir}")
            print_status(f"Details: {e}")
            return False

        # Extract ZIP
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        # Verify extraction
        extracted_files = list(extract_dir.rglob("*"))
        print_status(f"Extracted {len(extracted_files)} files")

        return True
    except zipfile.BadZipFile as e:
        print_status(f"ERROR: Invalid ZIP file: {e}")
        return False
    except Exception as e:
        print_status(f"ERROR: Failed to extract update: {e}")
        return False


def find_executable_in_extract(
    extract_dir: Path,
    names: list[str],
) -> Optional[Path]:
    """Find a matching executable in an extracted update directory.

    Args:
        extract_dir: Directory containing extracted update files.
        names: Candidate executable names to search for.

    Returns:
        Path to the first matching executable, or None if not found.
    """
    for name in names:
        direct_path = extract_dir / name
        if direct_path.exists():
            return direct_path
        matches = list(extract_dir.glob(f"**/{name}"))
        if matches:
            return matches[0]
    return None


def replace_executable(new_exe_path: Path, target_exe_path: Path) -> bool:
    """Replace old executable with new one.

    Args:
        new_exe_path: Path to new executable
        target_exe_path: Path where to place the new executable

    Returns:
        True if replacement succeeded, False otherwise
    """
    # Higher retry count for anti-virus scenarios (common with admin privileges)
    # AV software can lock executables for 10-30 seconds after process exit
    max_retries = 20
    retry_delay = 1.0  # Start with 1 second (AV scans need time)
    start_time = time.time()

    for attempt in range(max_retries):
        try:
            if attempt > 0:
                elapsed = time.time() - start_time
                print_status(
                    f"Retry attempt {attempt + 1}/{max_retries} (elapsed: {elapsed:.1f}s)..."
                )
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 1.5, 5.0)  # Exponential backoff, max 5s

            print_status(f"Replacing {target_exe_path.name} with new version")

            # Verify new exe exists
            if not new_exe_path.exists():
                print_status(f"ERROR: New executable not found: {new_exe_path}")
                return False

            # Remove old exe
            if target_exe_path.exists():
                target_exe_path.unlink()

            # Copy new exe
            shutil.copy2(new_exe_path, target_exe_path)
            print_status("Replacement successful")

            return True

        except PermissionError as e:
            # Windows file locking - retry
            if attempt < max_retries - 1:
                elapsed = time.time() - start_time
                print_status(
                    f"File locked (attempt {attempt + 1}/{max_retries}, elapsed: {elapsed:.1f}s), retrying..."
                )
                if attempt == 5:
                    print_status(
                        "Note: Anti-virus software may be scanning the executable..."
                    )
                    print_status("This can take 10-30 seconds with admin privileges")
                continue
            else:
                elapsed = time.time() - start_time
                print_status(
                    f"ERROR: Failed to replace executable after {max_retries} attempts ({elapsed:.1f}s): {e}"
                )
                print_status("File may be locked by anti-virus or another process")
                print_status("TROUBLESHOOTING:")
                print_status("  1. Check if anti-virus is running a scan")
                print_status("  2. Add install directory to AV exclusions")
                print_status("  3. Try update again when AV scan completes")
                return False

        except Exception as e:
            print_status(f"ERROR: Failed to replace executable: {e}")
            return False

    return False


def copy_executable(source_path: Path, target_path: Path, description: str) -> bool:
    """Copy an executable with retry logic for transient locks.

    Args:
        source_path: Path to the source executable
        target_path: Destination path for the copy
        description: Human-readable description for status logs

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
            print_status(f"Created {description}: {target_path.name}")
            return True
        except PermissionError:
            if attempt == max_retries - 1:
                print_status(
                    f"WARNING: Failed to create {description} due to file lock"
                )
                return False
        except Exception as e:
            print_status(f"WARNING: Failed to create {description}: {e}")
            return False

    return False


def remove_legacy_executable(legacy_path: Path, description: str) -> bool:
    """Remove a legacy executable with retry logic.

    Args:
        legacy_path: Path to the legacy executable
        description: Human-readable description for status logs

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
            print_status(f"Removed {description}: {legacy_path.name}")
            return True
        except PermissionError:
            if attempt == max_retries - 1:
                print_status(
                    f"WARNING: Failed to remove {description} due to file lock"
                )
                return False
        except Exception as e:
            print_status(f"WARNING: Failed to remove {description}: {e}")
            return False

    return False


def set_post_update_flag(exe_path: Path) -> None:
    """Set post-update flags in database before launching app.

    Sets two flags with different lifecycles:
    - post_update_no_browser: Signals app to skip browser auto-launch (cleared at startup)
    - post_update_show_toast: Triggers success toast in JavaScript (cleared after display)

    This separation ensures browser tabs reconnect instead of opening new ones,
    while still displaying the success message after page loads.

    Args:
        exe_path: Path to executable (used to find database)
    """
    try:
        # Database is in profiles/burndown.db relative to exe directory
        db_path = exe_path.parent / "profiles" / "burndown.db"

        if not db_path.exists():
            print_status(
                f"WARNING: Database not found at {db_path} - skipping flag set"
            )
            return

        print_status("Setting post-update flags in database")

        # Direct SQLite connection (no need for full backend initialization)
        conn = sqlite3.connect(str(db_path), timeout=10)
        cursor = conn.cursor()

        # Set two flags with different lifecycles:
        # 1. post_update_no_browser: Prevents browser auto-launch (cleared at startup)
        # 2. post_update_show_toast: Triggers success toast (cleared by JavaScript)
        cursor.execute(
            "INSERT OR REPLACE INTO app_state (key, value) VALUES (?, ?)",
            ("post_update_no_browser", "true"),
        )
        cursor.execute(
            "INSERT OR REPLACE INTO app_state (key, value) VALUES (?, ?)",
            ("post_update_show_toast", "true"),
        )
        conn.commit()
        conn.close()

        print_status("Post-update flags set successfully")
    except Exception as e:
        print_status(f"WARNING: Failed to set post-update flag: {e}")
        print_status("App will launch normally with browser auto-open")


def launch_application(exe_path: Path) -> bool:
    """Launch the updated application.

    Args:
        exe_path: Path to executable to launch

    Returns:
        True if launch succeeded, False otherwise
    """
    try:
        # Set database flag before launching to prevent duplicate browser tabs
        set_post_update_flag(exe_path)

        print_status(f"Launching {exe_path.name}")

        if sys.platform == "win32":
            # Windows: use DETACHED_PROCESS to launch without console
            DETACHED_PROCESS = 0x00000008
            subprocess.Popen(
                [str(exe_path)],
                creationflags=DETACHED_PROCESS,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            # Unix: use start_new_session
            subprocess.Popen(
                [str(exe_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

        print_status("Application launched successfully")
        return True
    except Exception as e:
        print_status(f"WARNING: Failed to launch application: {e}")
        print_status("You may need to launch the application manually")
        return False


def main() -> int:
    """Main updater logic.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    print_status("=" * 60)
    print_status("Burndown Updater")
    print_status("=" * 60)

    # Parse command line arguments (backward compatible)
    if len(sys.argv) < 4:
        print_status("ERROR: Invalid arguments")
        print_status(
            "Usage: updater.exe <current_exe> <update_zip> <app_pid> [--updater-exe <updater_exe>]"
        )
        return 1

    current_exe = Path(sys.argv[1])
    update_zip = Path(sys.argv[2])
    app_pid = int(sys.argv[3])

    # Check for --updater-exe flag (self-update support)
    updater_exe: Optional[Path] = None
    if len(sys.argv) >= 6 and sys.argv[4] == "--updater-exe":
        updater_exe = Path(sys.argv[5])
        print_status(f"Self-update mode enabled: will replace updater at {updater_exe}")

    print_status(f"Current executable: {current_exe}")
    print_status(f"Update ZIP: {update_zip}")
    print_status(f"App process ID: {app_pid}")
    if updater_exe:
        print_status(f"Updater executable: {updater_exe}")

    # Validate arguments
    if not update_zip.exists():
        print_status(f"ERROR: Update ZIP not found: {update_zip}")
        return 1

    # Step 1: Wait for app to exit
    if not wait_for_process_exit(app_pid, timeout=10):
        print_status("ERROR: Application didn't exit in time")
        print_status("Please close the application manually and run the updater again")
        return 2

    # Windows needs extra time to fully release file handles after process exit
    # Admin processes + anti-virus scanning can hold locks for 10-30 seconds
    print_status("Waiting for Windows to release file handles...")
    print_status("(Anti-virus may scan executable - this can take 10-30 seconds)")
    time.sleep(3.0)  # 3 second grace period (increased for AV scenarios)

    # Step 2: Backup current executable
    backup_path = backup_file(current_exe)
    if not backup_path:
        print_status("ERROR: Failed to create backup - aborting update")
        return 3

    # Step 3: Extract new version
    # Use unique directory name to avoid conflicts with concurrent updates or stale files
    import uuid

    extract_dir = (
        Path(tempfile.gettempdir()) / f"burndown_update_{uuid.uuid4().hex[:8]}"
    )
    if not extract_update(update_zip, extract_dir):
        print_status("ERROR: Failed to extract update - aborting")
        # Clean up temp directory on failure
        try:
            shutil.rmtree(extract_dir)
        except Exception:
            pass
        return 4

    # Find new app executable in extracted files
    app_exe_names = [MAIN_EXE_NAME]
    if current_exe.name not in app_exe_names:
        app_exe_names.append(current_exe.name)

    new_exe = find_executable_in_extract(extract_dir, app_exe_names)
    if not new_exe:
        print_status(
            "ERROR: New executable not found in ZIP: " + ", ".join(app_exe_names)
        )
        return 4
    print_status(f"Found new app executable: {new_exe}")

    # Step 4: Replace old app executable with new one
    if not replace_executable(new_exe, current_exe):
        print_status("ERROR: Failed to replace app executable - restoring backup")
        restore_from_backup(backup_path, current_exe)
        return 5

    print_status("App update completed successfully!")

    launch_exe = current_exe
    if current_exe.name != MAIN_EXE_NAME:
        main_exe_path = current_exe.parent / MAIN_EXE_NAME
        if copy_executable(current_exe, main_exe_path, "main executable"):
            launch_exe = main_exe_path
            if current_exe.name == LEGACY_MAIN_EXE_NAME:
                remove_legacy_executable(current_exe, "legacy main executable")

    # Step 5: Replace updater executable (if self-update requested)
    if updater_exe:
        print_status("Starting updater self-update...")

        # Backup current updater
        updater_backup = backup_file(updater_exe)
        if not updater_backup:
            print_status(
                "WARNING: Failed to create updater backup - skipping self-update"
            )
        else:
            # Find new updater in extracted files
            updater_names = [
                UPDATER_EXE_NAME,
                LEGACY_UPDATER_EXE_NAME,
                updater_exe.name,
            ]
            updater_names = list(dict.fromkeys(updater_names))

            new_updater = find_executable_in_extract(extract_dir, updater_names)
            if not new_updater:
                print_status(
                    "WARNING: New updater not found in ZIP: " + ", ".join(updater_names)
                )
                print_status("App has been updated, but updater remains at old version")
                # Remove updater backup since we're not updating it
                if updater_backup.exists():
                    updater_backup.unlink()
            else:
                print_status(f"Found new updater executable: {new_updater}")

                # Replace updater
                if not replace_executable(new_updater, updater_exe):
                    print_status("WARNING: Failed to replace updater executable")
                    print_status(
                        "App has been updated, but updater remains at old version"
                    )
                    # Restore updater backup
                    restore_from_backup(updater_backup, updater_exe)
                else:
                    print_status("Updater self-update completed successfully!")
                    if updater_exe.name != UPDATER_EXE_NAME:
                        updater_alias = updater_exe.parent / UPDATER_EXE_NAME
                        if copy_executable(updater_exe, updater_alias, "updater"):
                            if updater_exe.name == LEGACY_UPDATER_EXE_NAME:
                                remove_legacy_executable(
                                    updater_exe, "legacy updater executable"
                                )
                    # Remove updater backup after successful update
                    if updater_backup.exists():
                        updater_backup.unlink()

    print_status("All updates completed successfully!")

    legacy_main_path = current_exe.parent / LEGACY_MAIN_EXE_NAME
    if launch_exe.name == MAIN_EXE_NAME and legacy_main_path.exists():
        remove_legacy_executable(legacy_main_path, "legacy main executable")

    legacy_updater_path = current_exe.parent / LEGACY_UPDATER_EXE_NAME
    new_updater_path = current_exe.parent / UPDATER_EXE_NAME
    if new_updater_path.exists() and legacy_updater_path.exists():
        remove_legacy_executable(legacy_updater_path, "legacy updater executable")

    # Step 6: Launch updated application
    launch_application(launch_exe)

    # Step 7: Clean up
    try:
        print_status("Cleaning up temporary files...")

        # Remove app backup file after successful update
        if backup_path.exists():
            backup_path.unlink()
            print_status("Removed backup file")

        # Remove extraction directory
        if extract_dir.exists():
            shutil.rmtree(extract_dir)

        # Remove update ZIP file
        if update_zip.exists():
            update_zip.unlink()
            print_status("Removed update ZIP")

        # Clean up parent temp directories if empty
        for temp_folder in ["burndown_updater", "burndown_updates"]:
            temp_path = Path(update_zip.parent.parent) / temp_folder
            if temp_path.exists():
                try:
                    # Remove if empty or force remove
                    shutil.rmtree(temp_path)
                    print_status(f"Removed temp folder: {temp_folder}")
                except Exception:
                    pass  # May still have files from other sessions

        print_status("Cleanup complete")
    except Exception as e:
        print_status(f"Warning: Cleanup failed: {e}")

    print_status("=" * 60)
    print_status("Update process finished - you may close this window")
    print_status("=" * 60)

    # Brief delay so user can see final status
    time.sleep(1)

    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print_status("=" * 60)
        print_status(f"FATAL ERROR: {e}")
        print_status("=" * 60)
        import traceback

        traceback.print_exc()
        time.sleep(10)  # Keep window open so user can see error
        sys.exit(6)
