"""
Burndown Chart Updater

Standalone updater executable that replaces the main application with a new version.
This runs as a separate process after the main app exits.

Usage:
    BurndownChartUpdater.exe <current_exe> <update_zip> <app_pid>

Arguments:
    current_exe: Path to the current BurndownChart.exe to be replaced
    update_zip: Path to the ZIP file containing the new version
    app_pid: Process ID of the running app (to wait for exit)

Flow:
    1. Wait for app.exe to exit (or timeout after 10 seconds)
    2. Backup current exe to .bak file
    3. Extract new version from ZIP
    4. Replace old exe with new exe
    5. Restart the application
    6. Clean up temporary files

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
import time
import zipfile
import shutil
import subprocess
from pathlib import Path
from typing import Optional


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
    try:
        print_status(f"Restoring from backup: {backup_path.name}")

        # Remove corrupted file if it exists
        if target_path.exists():
            target_path.unlink()

        # Restore from backup
        shutil.copy2(backup_path, target_path)
        print_status("Restore successful")
        return True
    except Exception as e:
        print_status(f"ERROR: Failed to restore from backup: {e}")
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

        # Create extraction directory
        extract_dir.mkdir(parents=True, exist_ok=True)

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


def replace_executable(new_exe_path: Path, target_exe_path: Path) -> bool:
    """Replace old executable with new one.

    Args:
        new_exe_path: Path to new executable
        target_exe_path: Path where to place the new executable

    Returns:
        True if replacement succeeded, False otherwise
    """
    try:
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
    except Exception as e:
        print_status(f"ERROR: Failed to replace executable: {e}")
        return False


def launch_application(exe_path: Path) -> bool:
    """Launch the updated application.

    Args:
        exe_path: Path to executable to launch

    Returns:
        True if launch succeeded, False otherwise
    """
    try:
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
    print_status("Burndown Chart Updater")
    print_status("=" * 60)

    # Parse command line arguments
    if len(sys.argv) != 4:
        print_status("ERROR: Invalid arguments")
        print_status("Usage: updater.exe <current_exe> <update_zip> <app_pid>")
        return 1

    current_exe = Path(sys.argv[1])
    update_zip = Path(sys.argv[2])
    app_pid = int(sys.argv[3])

    print_status(f"Current executable: {current_exe}")
    print_status(f"Update ZIP: {update_zip}")
    print_status(f"App process ID: {app_pid}")

    # Validate arguments
    if not update_zip.exists():
        print_status(f"ERROR: Update ZIP not found: {update_zip}")
        return 1

    # Step 1: Wait for app to exit
    if not wait_for_process_exit(app_pid, timeout=10):
        print_status("ERROR: Application didn't exit in time")
        print_status("Please close the application manually and run the updater again")
        return 2

    # App uses os._exit() so file handles are released immediately
    # No additional delay needed with fast polling

    # Step 2: Backup current executable
    backup_path = backup_file(current_exe)
    if not backup_path:
        print_status("ERROR: Failed to create backup - aborting update")
        return 3

    # Step 3: Extract new version
    extract_dir = update_zip.parent / "update_temp"
    if not extract_update(update_zip, extract_dir):
        print_status("ERROR: Failed to extract update - aborting")
        return 4

    # Find new executable in extracted files
    new_exe_candidates = list(extract_dir.glob(f"**/{current_exe.name}"))
    if not new_exe_candidates:
        print_status(f"ERROR: New executable not found in ZIP: {current_exe.name}")
        return 4

    new_exe = new_exe_candidates[0]
    print_status(f"Found new executable: {new_exe}")

    # Step 4: Replace old executable with new one
    if not replace_executable(new_exe, current_exe):
        print_status("ERROR: Failed to replace executable - restoring backup")
        restore_from_backup(backup_path, current_exe)
        return 5

    print_status("Update completed successfully!")

    # Step 5: Launch updated application
    launch_application(current_exe)

    # Step 6: Clean up
    try:
        print_status("Cleaning up temporary files...")

        # Remove backup file after successful update
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
