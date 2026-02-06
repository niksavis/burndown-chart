"""
Integration test for executable launch smoke tests.

Tests that the built executable can launch successfully without errors.
This is a basic smoke test to ensure the packaging process works correctly.

User Story: US3 - Automated Build Process
Phase: 11 - Testing & Validation
"""

import os
import subprocess
import time
import sys
from pathlib import Path
import pytest


def test_executable_exists():
    """Test that the main executable exists in dist/ directory.

    This verifies the build process completed successfully.
    """
    project_root = Path(__file__).parent.parent.parent
    exe_path = project_root / "dist" / "Burndown.exe"

    if not exe_path.exists():
        pytest.skip("Executable not found - build required before running this test")

    assert exe_path.exists(), f"Executable not found at {exe_path}"
    assert exe_path.is_file(), f"{exe_path} exists but is not a file"
    assert exe_path.stat().st_size > 0, f"{exe_path} is empty"


def test_updater_executable_exists():
    """Test that the updater executable exists in dist/ directory.

    This verifies the two-executable architecture is properly built.
    """
    project_root = Path(__file__).parent.parent.parent
    updater_path = project_root / "dist" / "BurndownUpdater.exe"

    if not updater_path.exists():
        pytest.skip(
            "Updater executable not found - build required before running this test"
        )

    assert updater_path.exists(), f"Updater executable not found at {updater_path}"
    assert updater_path.is_file(), f"{updater_path} exists but is not a file"
    assert updater_path.stat().st_size > 0, f"{updater_path} is empty"


@pytest.mark.skipif(
    sys.platform != "win32", reason="Executable tests only run on Windows"
)
def test_executable_launches_without_crash():
    """Test that the executable launches and doesn't immediately crash.

    This is a smoke test - we launch the process, wait briefly to ensure
    it doesn't crash immediately, then terminate it.

    Note: This test requires the executable to be built first using build.ps1
    """
    project_root = Path(__file__).parent.parent.parent
    exe_path = project_root / "dist" / "Burndown.exe"

    if not exe_path.exists():
        pytest.skip("Executable not found - build required before running this test")

    # Launch executable with BURNDOWN_NO_BROWSER to prevent browser opening
    # Extend environment (don't replace it) to preserve system vars like TEMP
    env = os.environ.copy()
    env["BURNDOWN_NO_BROWSER"] = "1"
    process = subprocess.Popen(
        [str(exe_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        # Don't use CREATE_NEW_CONSOLE - it makes cleanup harder
        creationflags=0,
    )

    try:
        # Wait 5 seconds to ensure app doesn't crash immediately
        time.sleep(5)

        # Check if process is still running
        poll_result = process.poll()
        assert poll_result is None, (
            f"Executable crashed immediately (exit code: {poll_result})"
        )

        # If we got here, the app launched successfully

    finally:
        # Clean up: terminate the process and all children
        try:
            # Use psutil if available for better process tree killing
            try:
                import psutil

                parent = psutil.Process(process.pid)
                children = parent.children(recursive=True)

                # Terminate all children first
                for child in children:
                    try:
                        child.terminate()
                    except psutil.NoSuchProcess:
                        pass

                # Terminate parent
                parent.terminate()

                # Wait for graceful shutdown
                gone, alive = psutil.wait_procs([parent] + children, timeout=3)

                # Force kill any survivors
                for p in alive:
                    try:
                        p.kill()
                    except psutil.NoSuchProcess:
                        pass

            except ImportError:
                # Fallback: basic terminate/kill
                process.terminate()
                process.wait(timeout=3)

        except subprocess.TimeoutExpired:
            # Force kill if graceful termination fails
            process.kill()
            process.wait(timeout=2)
        except Exception:
            # Last resort: force kill
            try:
                process.kill()
            except Exception:
                pass  # Process might already be dead


@pytest.mark.skipif(
    sys.platform != "win32", reason="Executable tests only run on Windows"
)
def test_updater_executable_shows_usage():
    """Test that updater executable runs and shows usage message.

    When run without arguments, the updater should display usage info
    and exit with code 1 (invalid arguments).
    """
    project_root = Path(__file__).parent.parent.parent
    updater_path = project_root / "dist" / "BurndownUpdater.exe"

    if not updater_path.exists():
        pytest.skip(
            "Updater executable not found - build required before running this test"
        )

    # Run updater without arguments (should show usage)
    result = subprocess.run(
        [str(updater_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=10,
    )

    # Updater should exit with code 1 (invalid arguments)
    assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}"

    # Output should contain usage message
    combined_output = result.stdout + result.stderr
    assert (
        "Usage:" in combined_output or "ERROR: Invalid arguments" in combined_output
    ), "Expected usage message in output"


def test_build_spec_files_exist():
    """Test that PyInstaller spec files exist and are valid.

    This ensures the build configuration is properly committed.
    """
    project_root = Path(__file__).parent.parent.parent
    build_dir = project_root / "build"

    app_spec = build_dir / "app.spec"
    updater_spec = build_dir / "updater.spec"

    assert app_spec.exists(), f"app.spec not found at {app_spec}"
    assert updater_spec.exists(), f"updater.spec not found at {updater_spec}"

    # Verify spec files contain required PyInstaller directives
    app_spec_content = app_spec.read_text(encoding="utf-8")
    assert "Analysis(" in app_spec_content, "app.spec missing Analysis section"
    assert "EXE(" in app_spec_content, "app.spec missing EXE section"

    updater_spec_content = updater_spec.read_text(encoding="utf-8")
    assert "Analysis(" in updater_spec_content, "updater.spec missing Analysis section"
    assert "EXE(" in updater_spec_content, "updater.spec missing EXE section"


def test_build_script_exists():
    """Test that the build script exists and is executable.

    This ensures developers can build the executables.
    """
    project_root = Path(__file__).parent.parent.parent
    build_script = project_root / "build" / "build.ps1"

    assert build_script.exists(), f"Build script not found at {build_script}"
    assert build_script.is_file(), f"{build_script} is not a file"

    # Verify script contains expected build steps
    script_content = build_script.read_text(encoding="utf-8")
    assert "PyInstaller" in script_content, "Build script missing PyInstaller reference"
    assert "app.spec" in script_content, "Build script missing app.spec reference"
