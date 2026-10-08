import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

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
    extract_update,
    find_executable_in_extract,
    verify_checksums,
)

APP_NAME = "Burndown"
MAIN_EXE_NAME = "Burndown.exe"
LEGACY_MAIN_EXE_NAME = "BurndownChart.exe"
UPDATER_EXE_NAME = "BurndownUpdater.exe"
LEGACY_UPDATER_EXE_NAME = "BurndownChartUpdater.exe"
FILE_HANDLE_RELEASE_GRACE_SECONDS = 3.0
ERROR_WINDOW_HOLD_SECONDS = 10


def print_status(message: str) -> None:

    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


def set_post_update_flag(exe_path: Path) -> None:

    try:
        db_path = exe_path.parent / "profiles" / "burndown.db"

        if not db_path.exists():
            print_status(
                f"WARNING: Database not found at {db_path} - skipping flag set"
            )
            return

        print_status("Setting post-update flags in database")

        conn = sqlite3.connect(str(db_path), timeout=10)
        cursor = conn.cursor()

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

    try:
        set_post_update_flag(exe_path)

        print_status(f"Launching {exe_path.name}")

        if sys.platform == "win32":
            DETACHED_PROCESS = 0x00000008
            subprocess.Popen(
                [str(exe_path)],
                creationflags=DETACHED_PROCESS,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
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

    print_status("=" * 60)
    print_status("Burndown Updater")
    print_status("=" * 60)

    if len(sys.argv) < 4:
        print_status("ERROR: Invalid arguments")
        print_status(
            "Usage: updater.exe <current_exe> <update_zip> <app_pid> "
            "[--updater-exe <updater_exe>]"
        )
        return 1

    current_exe = Path(sys.argv[1])
    update_zip = Path(sys.argv[2])
    app_pid = int(sys.argv[3])

    updater_exe: Path | None = None
    if len(sys.argv) >= 6 and sys.argv[4] == "--updater-exe":
        updater_exe = Path(sys.argv[5])
        print_status(f"Self-update mode enabled: will replace updater at {updater_exe}")

    print_status(f"Current executable: {current_exe}")
    print_status(f"Update ZIP: {update_zip}")
    print_status(f"App process ID: {app_pid}")
    if updater_exe:
        print_status(f"Updater executable: {updater_exe}")

    if not update_zip.exists():
        print_status(f"ERROR: Update ZIP not found: {update_zip}")
        return 1

    if not wait_for_process_exit(app_pid, print_status, timeout=10):
        print_status("ERROR: Application didn't exit in time")
        print_status("Please close the application manually and run the updater again")
        return 2

    print_status("Waiting for Windows to release file handles...")
    print_status("(Anti-virus may scan executable - this can take 10-30 seconds)")
    time.sleep(FILE_HANDLE_RELEASE_GRACE_SECONDS)

    backup_path = backup_file(current_exe, print_status)
    if not backup_path:
        print_status("ERROR: Failed to create backup - aborting update")
        return 3

    import uuid  # noqa: PLC0415

    extract_dir = (
        Path(tempfile.gettempdir()) / f"burndown_update_{uuid.uuid4().hex[:8]}"
    )
    if not extract_update(update_zip, extract_dir, print_status):
        print_status("ERROR: Failed to extract update - aborting")
        try:
            shutil.rmtree(extract_dir)
        except Exception:
            pass
        return 4

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
                "WARNING: New updater not found for checksum verification; "
                "updater may remain at old version"
            )

    if not verify_checksums(extract_dir, expected_files, print_status):
        print_status("ERROR: Integrity check failed - aborting update")
        try:
            shutil.rmtree(extract_dir)
        except Exception:
            pass
        return 4

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

    if updater_exe:
        print_status("Starting updater self-update...")

        updater_backup = backup_file(updater_exe, print_status)
        if not updater_backup:
            print_status(
                "WARNING: Failed to create updater backup - skipping self-update"
            )
        else:
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
                if updater_backup.exists():
                    updater_backup.unlink()
            else:
                print_status(f"Found new updater executable: {new_updater}")

                if not replace_executable(new_updater, updater_exe, print_status):
                    print_status("WARNING: Failed to replace updater executable")
                    print_status(
                        "App has been updated, but updater remains at old version"
                    )
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

    launch_application(launch_exe)

    try:
        print_status("Cleaning up temporary files...")

        if backup_path.exists():
            backup_path.unlink()
            print_status("Removed backup file")

        if extract_dir.exists():
            shutil.rmtree(extract_dir)

        if update_zip.exists():
            update_zip.unlink()
            print_status("Removed update ZIP")

        for temp_folder in ["burndown_updater", "burndown_updates"]:
            temp_path = Path(update_zip.parent.parent) / temp_folder
            if temp_path.exists():
                try:
                    shutil.rmtree(temp_path)
                    print_status(f"Removed temp folder: {temp_folder}")
                except Exception:
                    pass

        print_status("Cleanup complete")
    except Exception as e:
        print_status(f"Warning: Cleanup failed: {e}")

    print_status("=" * 60)
    print_status("Update process finished - you may close this window")
    print_status("=" * 60)

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
        time.sleep(ERROR_WINDOW_HOLD_SECONDS)
        sys.exit(6)
