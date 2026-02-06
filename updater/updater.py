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

import sys
import tempfile
import time
import shutil
import subprocess
import sqlite3
from pathlib import Path
from typing import Optional

from updater.file_ops import (
    backup_file,
    copy_executable,
    remove_legacy_executable,
    replace_executable,
    restore_from_backup,
)
from updater.process_utils import wait_for_process_exit
from updater.support_files import SUPPORT_FILE_NAMES, replace_support_files
from updater.zip_utils import (
    find_executable_in_extract,
    extract_update,
    verify_checksums,
)

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
    if not wait_for_process_exit(app_pid, print_status, timeout=10):
        print_status("ERROR: Application didn't exit in time")
        print_status("Please close the application manually and run the updater again")
        return 2

    # Windows needs extra time to fully release file handles after process exit
    # Admin processes + anti-virus scanning can hold locks for 10-30 seconds
    print_status("Waiting for Windows to release file handles...")
    print_status("(Anti-virus may scan executable - this can take 10-30 seconds)")
    time.sleep(3.0)  # 3 second grace period (increased for AV scenarios)

    # Step 2: Backup current executable
    backup_path = backup_file(current_exe, print_status)
    if not backup_path:
        print_status("ERROR: Failed to create backup - aborting update")
        return 3

    # Step 3: Extract new version
    # Use unique directory name to avoid conflicts with concurrent updates or stale files
    import uuid

    extract_dir = (
        Path(tempfile.gettempdir()) / f"burndown_update_{uuid.uuid4().hex[:8]}"
    )
    if not extract_update(update_zip, extract_dir, print_status):
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

    expected_files = [new_exe.name, *SUPPORT_FILE_NAMES]
    if updater_exe:
        updater_names = [
            UPDATER_EXE_NAME,
            LEGACY_UPDATER_EXE_NAME,
            updater_exe.name,
        ]
        new_updater_for_checksum = find_executable_in_extract(
            extract_dir, updater_names
        )
        if new_updater_for_checksum:
            expected_files.append(new_updater_for_checksum.name)
        else:
            print_status(
                "WARNING: New updater not found for checksum verification; updater may remain at old version"
            )

    if not verify_checksums(extract_dir, expected_files, print_status):
        print_status("ERROR: Integrity check failed - aborting update")
        try:
            shutil.rmtree(extract_dir)
        except Exception:
            pass
        return 4

    # Step 4: Replace old app executable with new one
    if not replace_executable(new_exe, current_exe, print_status):
        print_status("ERROR: Failed to replace app executable - restoring backup")
        restore_from_backup(backup_path, current_exe, print_status)
        return 5

    print_status("App update completed successfully!")

    replace_support_files(extract_dir, current_exe.parent, print_status)

    launch_exe = current_exe
    if current_exe.name != MAIN_EXE_NAME:
        main_exe_path = current_exe.parent / MAIN_EXE_NAME
        if copy_executable(current_exe, main_exe_path, "main executable", print_status):
            launch_exe = main_exe_path
            if current_exe.name == LEGACY_MAIN_EXE_NAME:
                remove_legacy_executable(
                    current_exe,
                    "legacy main executable",
                    print_status,
                )

    # Step 5: Replace updater executable (if self-update requested)
    if updater_exe:
        print_status("Starting updater self-update...")

        # Backup current updater
        updater_backup = backup_file(updater_exe, print_status)
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
                if not replace_executable(new_updater, updater_exe, print_status):
                    print_status("WARNING: Failed to replace updater executable")
                    print_status(
                        "App has been updated, but updater remains at old version"
                    )
                    # Restore updater backup
                    restore_from_backup(updater_backup, updater_exe, print_status)
                else:
                    print_status("Updater self-update completed successfully!")
                    if updater_exe.name != UPDATER_EXE_NAME:
                        updater_alias = updater_exe.parent / UPDATER_EXE_NAME
                        if copy_executable(
                            updater_exe,
                            updater_alias,
                            "updater",
                            print_status,
                        ):
                            if updater_exe.name == LEGACY_UPDATER_EXE_NAME:
                                remove_legacy_executable(
                                    updater_exe,
                                    "legacy updater executable",
                                    print_status,
                                )
                    # Remove updater backup after successful update
                    if updater_backup.exists():
                        updater_backup.unlink()

    print_status("All updates completed successfully!")

    legacy_main_path = current_exe.parent / LEGACY_MAIN_EXE_NAME
    if launch_exe.name == MAIN_EXE_NAME and legacy_main_path.exists():
        remove_legacy_executable(
            legacy_main_path,
            "legacy main executable",
            print_status,
        )

    legacy_updater_path = current_exe.parent / LEGACY_UPDATER_EXE_NAME
    new_updater_path = current_exe.parent / UPDATER_EXE_NAME
    if new_updater_path.exists() and legacy_updater_path.exists():
        remove_legacy_executable(
            legacy_updater_path,
            "legacy updater executable",
            print_status,
        )

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
