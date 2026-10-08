import os
import subprocess
import sys
import time
from pathlib import Path

import pytest


def test_executable_exists():

    project_root = Path(__file__).parent.parent.parent
    exe_path = project_root / "dist" / "Burndown.exe"

    if not exe_path.exists():
        pytest.skip("Executable not found - build required before running this test")

    assert exe_path.exists(), f"Executable not found at {exe_path}"
    assert exe_path.is_file(), f"{exe_path} exists but is not a file"
    assert exe_path.stat().st_size > 0, f"{exe_path} is empty"


def test_updater_executable_exists():

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

    project_root = Path(__file__).parent.parent.parent
    exe_path = project_root / "dist" / "Burndown.exe"

    if not exe_path.exists():
        pytest.skip("Executable not found - build required before running this test")

    env = os.environ.copy()
    env["BURNDOWN_NO_BROWSER"] = "1"
    process = subprocess.Popen(
        [str(exe_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        creationflags=0,
    )

    try:
        time.sleep(5)

        poll_result = process.poll()
        assert poll_result is None, (
            f"Executable crashed immediately (exit code: {poll_result})"
        )

    finally:
        try:
            try:
                import psutil

                parent = psutil.Process(process.pid)
                children = parent.children(recursive=True)

                for child in children:
                    try:
                        child.terminate()
                    except psutil.NoSuchProcess:
                        pass

                parent.terminate()

                gone, alive = psutil.wait_procs([parent] + children, timeout=3)

                for p in alive:
                    try:
                        p.kill()
                    except psutil.NoSuchProcess:
                        pass

            except ImportError:
                process.terminate()
                process.wait(timeout=3)

        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass


@pytest.mark.skipif(
    sys.platform != "win32", reason="Executable tests only run on Windows"
)
def test_updater_executable_shows_usage():

    project_root = Path(__file__).parent.parent.parent
    updater_path = project_root / "dist" / "BurndownUpdater.exe"

    if not updater_path.exists():
        pytest.skip(
            "Updater executable not found - build required before running this test"
        )

    result = subprocess.run(
        [str(updater_path)],
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}"

    combined_output = result.stdout + result.stderr
    assert (
        "Usage:" in combined_output or "ERROR: Invalid arguments" in combined_output
    ), "Expected usage message in output"


def test_build_spec_files_exist():

    project_root = Path(__file__).parent.parent.parent
    build_dir = project_root / "build"

    app_spec = build_dir / "app.spec"
    updater_spec = build_dir / "updater.spec"

    assert app_spec.exists(), f"app.spec not found at {app_spec}"
    assert updater_spec.exists(), f"updater.spec not found at {updater_spec}"

    app_spec_content = app_spec.read_text(encoding="utf-8")
    assert "Analysis(" in app_spec_content, "app.spec missing Analysis section"
    assert "EXE(" in app_spec_content, "app.spec missing EXE section"

    updater_spec_content = updater_spec.read_text(encoding="utf-8")
    assert "Analysis(" in updater_spec_content, "updater.spec missing Analysis section"
    assert "EXE(" in updater_spec_content, "updater.spec missing EXE section"


def test_build_script_exists():

    project_root = Path(__file__).parent.parent.parent
    build_script = project_root / "build" / "build.ps1"

    assert build_script.exists(), f"Build script not found at {build_script}"
    assert build_script.is_file(), f"{build_script} is not a file"

    script_content = build_script.read_text(encoding="utf-8")
    assert "PyInstaller" in script_content, "Build script missing PyInstaller reference"
    assert "app.spec" in script_content, "Build script missing app.spec reference"
