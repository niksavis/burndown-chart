import sys
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.fixture(scope="function")
def temp_database():

    temp_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_db_path = Path(temp_db_file.name)
    temp_db_file.close()

    from data.migration.schema_manager import initialize_schema

    initialize_schema(db_path=temp_db_path)

    db_patches = [
        patch("data.database.DB_PATH", temp_db_path),
        patch("data.persistence.factory.DEFAULT_SQLITE_PATH", str(temp_db_path)),
    ]

    for p in db_patches:
        p.start()

    import data.persistence.factory as factory

    factory._backend_instance = None

    yield temp_db_path

    factory._backend_instance = None

    for p in db_patches:
        p.stop()

    if temp_db_path.exists():
        temp_db_path.unlink()


@pytest.fixture(scope="function")
def isolate_test_data(temp_database):

    _tmpdir = tempfile.TemporaryDirectory(prefix="burndown_test_")
    temp_root = _tmpdir.name
    temp_profiles_dir = Path(temp_root) / "profiles"
    temp_profiles_dir.mkdir(parents=True, exist_ok=True)
    temp_profiles_file = temp_profiles_dir / "profiles.json"

    temp_project_data = Path(temp_root) / "project_data.json"
    temp_jira_cache = Path(temp_root) / "jira_cache.json"
    temp_metrics_snapshots = Path(temp_root) / "metrics_snapshots.json"
    temp_app_settings = Path(temp_root) / "app_settings.json"
    temp_app_settings = Path(temp_root) / "app_settings.json"

    patches = [
        patch("data.profile_manager.PROFILES_DIR", temp_profiles_dir),
    ]

    try:
        from data import persistence

        if hasattr(persistence, "PROJECT_DATA_FILE"):
            patches.append(
                patch("data.persistence.PROJECT_DATA_FILE", temp_project_data)
            )
        if hasattr(persistence, "SETTINGS_FILE"):
            patches.append(patch("data.persistence.SETTINGS_FILE", temp_app_settings))
    except ImportError:
        pass

    try:
        from data import (
            metrics_snapshots,  # noqa: F401 - import needed for hasattr check
        )

        patches.append(
            patch(
                "data.metrics_snapshots._get_snapshots_file_path",
                return_value=temp_metrics_snapshots,
            )
        )
    except ImportError:
        pass

    for p in patches:
        p.start()

    yield {
        "temp_root": temp_root,
        "profiles_dir": temp_profiles_dir,
        "profiles_file": temp_profiles_file,
        "project_data": temp_project_data,
        "jira_cache": temp_jira_cache,
        "metrics_snapshots": temp_metrics_snapshots,
        "app_settings": temp_app_settings,
    }

    for p in patches:
        p.stop()

    _tmpdir.cleanup()


@pytest.fixture(scope="function")
def live_server(isolate_test_data):

    import app as dash_app

    app = dash_app.app
    server_port = 8051
    server_url = f"http://127.0.0.1:{server_port}"

    def run_server():
        import waitress

        waitress.serve(
            app.server,
            host="127.0.0.1",
            port=server_port,
            threads=1,
            channel_timeout=30,
            _quiet=True,
        )

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    max_retries = 30
    for _i in range(max_retries):
        try:
            import socket

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(("127.0.0.1", server_port))
            sock.close()
            if result == 0:
                time.sleep(1)
                break
        except Exception:
            pass
        time.sleep(0.5)
    else:
        raise RuntimeError(f"Server failed to start after {max_retries * 0.5} seconds")

    yield server_url


@pytest.fixture(scope="function")
def temp_log_dir():

    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture(scope="function")
def temp_cache_dir():

    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


pytest_plugins = ["tests.utils.dashboard_test_fixtures"]
