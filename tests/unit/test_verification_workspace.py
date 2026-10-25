import os
import subprocess
import sys
import tempfile
from pathlib import Path


def test_offline_runner_isolates_collection_before_application_imports() -> None:
    source = """
import os
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch
from utils.business_time import now
from utils.runtime import demo_mode, profiles_directory

workspace = Path(os.environ['BURNDOWN_TEST_WORKSPACE'])
assert not demo_mode()
assert profiles_directory() == workspace
assert abs((now(UTC) - datetime.now(UTC)).total_seconds()) < 2
with patch('data.update_cleanup.cleanup_orphaned_temp_updaters') as cleanup:
    import app
    cleanup.assert_not_called()
from data.database import DB_PATH
from configuration.logging_config import DEFAULT_LOG_DIR
assert DB_PATH == workspace / 'burndown.db'
assert Path(DEFAULT_LOG_DIR) == workspace / 'logs'
assert Path(app.cache.directory) == workspace / 'cache'
assert app.update_check_thread.daemon

def test_collected_application():
    assert app.app.server is not None

def test_normal_database_is_refused_before_open():
    import sqlite3
    import pytest
    normal = Path.cwd() / 'profiles' / 'burndown.db'
    with pytest.raises(PermissionError, match='normal database'):
        sqlite3.connect(str(normal))
    with pytest.raises(PermissionError, match='normal database'):
        sqlite3.connect(normal.as_uri(), uri=True)
"""
    with tempfile.TemporaryDirectory() as directory:
        probe = Path(directory) / "test_collection.py"
        probe.write_text(source, encoding="utf-8")
        environment = os.environ.copy()
        environment["BURNDOWN_DEMO_MODE"] = "1"
        environment["BURNDOWN_DEMO_WORKSPACE"] = str(Path(directory) / "unused-demo")
        environment["BURNDOWN_AS_OF"] = "2026-01-29T12:00:00+00:00"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "devtools.offline_pytest",
                str(probe),
                "-q",
                "--no-cov",
            ],
            capture_output=True,
            text=True,
            env=environment,
            timeout=60,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "2 passed" in result.stdout
        assert not (Path(directory) / "unused-demo").exists()
