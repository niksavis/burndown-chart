import os
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.mark.parametrize("existing_file", [False, True])
def test_startup_initializes_missing_and_empty_databases(existing_file: bool) -> None:
    from data.migration.migrator import run_migration_if_needed

    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / "burndown.db"
        if existing_file:
            sqlite3.connect(database).close()
        with patch("data.migration.migrator.is_migration_needed", return_value=False):
            assert run_migration_if_needed(db_path=database)
        with closing(sqlite3.connect(database)) as connection, connection:
            tables = connection.execute(
                "SELECT name FROM sqlite_master WHERE type = ?", ("table",)
            ).fetchall()
        assert ("profiles",) in tables
        assert ("app_state",) in tables


def _build_database(workspace: Path) -> None:
    with closing(sqlite3.connect(workspace / "burndown.db")) as connection, connection:
        connection.execute("CREATE TABLE app_state (key TEXT PRIMARY KEY, value TEXT)")
        connection.execute(
            "INSERT INTO app_state VALUES (?, ?)", ("demo_seed_version", "v1")
        )


def test_seed_is_published_once_and_preserves_edits() -> None:
    from utils.demo_workspace import exclusive_workspace, publish_demo_database

    with tempfile.TemporaryDirectory() as directory:
        workspace = Path(directory)
        with exclusive_workspace(workspace):
            assert publish_demo_database(workspace, _build_database)
            with (
                closing(sqlite3.connect(workspace / "burndown.db")) as connection,
                connection,
            ):
                connection.execute(
                    "INSERT INTO app_state VALUES (?, ?)", ("edited", "yes")
                )
            assert not publish_demo_database(workspace, _build_database)
        with (
            closing(sqlite3.connect(workspace / "burndown.db")) as connection,
            connection,
        ):
            assert connection.execute(
                "SELECT value FROM app_state WHERE key = ?", ("edited",)
            ).fetchone() == ("yes",)


def test_interrupted_seed_is_not_published_and_can_restart() -> None:
    from utils.demo_workspace import exclusive_workspace, publish_demo_database

    def interrupted(workspace: Path) -> None:
        _build_database(workspace)
        raise RuntimeError("Interrupted")

    with tempfile.TemporaryDirectory() as directory:
        workspace = Path(directory)
        with exclusive_workspace(workspace):
            with pytest.raises(RuntimeError, match="Interrupted"):
                publish_demo_database(workspace, interrupted)
            assert not (workspace / "burndown.db").exists()
            assert publish_demo_database(workspace, _build_database)


def test_workspace_refuses_unmarked_data_and_reset() -> None:
    from utils.demo_workspace import (
        exclusive_workspace,
        publish_demo_database,
        reset_demo_workspace,
    )

    with tempfile.TemporaryDirectory() as directory:
        workspace = Path(directory)
        sentinel = workspace / "keep.txt"
        sentinel.write_text("owned by developer", encoding="utf-8")
        with pytest.raises(ValueError, match="unmarked"):
            with exclusive_workspace(workspace):
                publish_demo_database(workspace, _build_database)
        with pytest.raises(ValueError, match="marked"):
            reset_demo_workspace(workspace)
        assert sentinel.read_text(encoding="utf-8") == "owned by developer"
        assert not (workspace / ".demo.lock").exists()


def test_running_workspace_refuses_second_owner_and_reset_is_guarded() -> None:
    from utils.demo_workspace import (
        exclusive_workspace,
        publish_demo_database,
        reset_demo_workspace,
    )

    with tempfile.TemporaryDirectory() as directory:
        workspace = Path(directory)
        with exclusive_workspace(workspace):
            assert publish_demo_database(workspace, _build_database)
            with pytest.raises(RuntimeError, match="in use"):
                with exclusive_workspace(workspace):
                    pytest.fail("Second owner acquired an active workspace")
        with exclusive_workspace(workspace):
            reset_demo_workspace(workspace)
            assert not (workspace / "burndown.db").exists()


def test_business_date_is_fixed_without_freezing_operational_time(monkeypatch) -> None:
    from utils.business_time import now

    monkeypatch.setenv("BURNDOWN_DEMO_MODE", "1")
    monkeypatch.setenv("BURNDOWN_AS_OF", "2026-01-29T12:00:00+00:00")
    assert now() == datetime(2026, 1, 29, 12)
    assert now(UTC) == datetime(2026, 1, 29, 12, tzinfo=UTC)
    assert datetime.now(UTC) != now(UTC)
    monkeypatch.delenv("BURNDOWN_DEMO_MODE")
    assert abs((now(UTC) - datetime.now(UTC)).total_seconds()) < 2


@pytest.mark.parametrize("host", ["example.com", "192.0.2.1", "::"])
def test_offline_policy_refuses_external_network_before_dns(host: str) -> None:
    script = """
import socket
import sys
from utils.offline import install_offline_policy, OfflineNetworkError
install_offline_policy()
try:
    socket.getaddrinfo(sys.argv[1], 443)
except OfflineNetworkError:
    print('refused')
else:
    raise SystemExit('external network was allowed')
assert socket.getaddrinfo('127.0.0.1', 8050)
"""
    result = subprocess.run(
        [sys.executable, "-", host],
        input=script,
        capture_output=True,
        text=True,
        check=True,
        env=os.environ.copy(),
        timeout=10,
    )
    assert result.stdout.strip() == "refused"


def test_installation_context_uses_only_selected_workspace(monkeypatch) -> None:
    from data.installation_context import InstallationContext

    with tempfile.TemporaryDirectory() as directory:
        monkeypatch.setenv("BURNDOWN_DEMO_MODE", "1")
        monkeypatch.setenv("BURNDOWN_DEMO_WORKSPACE", directory)
        context = InstallationContext.detect()
        assert context.database_path == Path(directory) / "burndown.db"
        assert context.logs_path == Path(directory) / "logs"
