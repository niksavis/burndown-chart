import tempfile
from pathlib import Path

import pytest

from data.persistence.sqlite_backend import SQLiteBackend
from data.version_tracker import check_and_update_version


@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".db") as f:
        temp_path = Path(f.name)

    from data.migration.schema_manager import initialize_schema

    initialize_schema(temp_path)

    yield temp_path

    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def backend_with_temp_db(temp_db):
    return SQLiteBackend(str(temp_db))


def test_check_and_update_version_first_run(temp_db, backend_with_temp_db, monkeypatch):
    monkeypatch.setattr(
        "data.version_tracker.get_backend", lambda: backend_with_temp_db
    )
    monkeypatch.setattr("data.version_tracker.__version__", "2.5.4")

    version_changed, previous_version, current_version = check_and_update_version()

    assert version_changed is False
    assert previous_version is None
    assert current_version == "2.5.4"

    stored_version = backend_with_temp_db.get_app_state("last_run_version")
    assert stored_version == "2.5.4"


def test_check_and_update_version_no_change(temp_db, backend_with_temp_db, monkeypatch):
    backend_with_temp_db.set_app_state("last_run_version", "2.5.4")

    monkeypatch.setattr(
        "data.version_tracker.get_backend", lambda: backend_with_temp_db
    )
    monkeypatch.setattr("data.version_tracker.__version__", "2.5.4")

    version_changed, previous_version, current_version = check_and_update_version()

    assert version_changed is False
    assert previous_version == "2.5.4"
    assert current_version == "2.5.4"

    stored_version = backend_with_temp_db.get_app_state("last_run_version")
    assert stored_version == "2.5.4"


def test_check_and_update_version_changed(temp_db, backend_with_temp_db, monkeypatch):
    backend_with_temp_db.set_app_state("last_run_version", "2.5.3")

    monkeypatch.setattr(
        "data.version_tracker.get_backend", lambda: backend_with_temp_db
    )
    monkeypatch.setattr("data.version_tracker.__version__", "2.5.4")

    version_changed, previous_version, current_version = check_and_update_version()

    assert version_changed is True
    assert previous_version == "2.5.3"
    assert current_version == "2.5.4"

    stored_version = backend_with_temp_db.get_app_state("last_run_version")
    assert stored_version == "2.5.4"


def test_check_and_update_version_major_change(
    temp_db, backend_with_temp_db, monkeypatch
):
    backend_with_temp_db.set_app_state("last_run_version", "2.5.4")

    monkeypatch.setattr(
        "data.version_tracker.get_backend", lambda: backend_with_temp_db
    )
    monkeypatch.setattr("data.version_tracker.__version__", "3.0.0")

    version_changed, previous_version, current_version = check_and_update_version()

    assert version_changed is True
    assert previous_version == "2.5.4"
    assert current_version == "3.0.0"

    stored_version = backend_with_temp_db.get_app_state("last_run_version")
    assert stored_version == "3.0.0"


def test_check_and_update_version_downgrade(temp_db, backend_with_temp_db, monkeypatch):
    backend_with_temp_db.set_app_state("last_run_version", "2.5.4")

    monkeypatch.setattr(
        "data.version_tracker.get_backend", lambda: backend_with_temp_db
    )
    monkeypatch.setattr("data.version_tracker.__version__", "2.5.3")

    version_changed, previous_version, current_version = check_and_update_version()

    assert version_changed is True
    assert previous_version == "2.5.4"
    assert current_version == "2.5.3"

    stored_version = backend_with_temp_db.get_app_state("last_run_version")
    assert stored_version == "2.5.3"


def test_check_and_update_version_error_handling(backend_with_temp_db, monkeypatch):

    def mock_get_app_state(key):
        raise RuntimeError("Database error")

    monkeypatch.setattr(backend_with_temp_db, "get_app_state", mock_get_app_state)
    monkeypatch.setattr(
        "data.version_tracker.get_backend", lambda: backend_with_temp_db
    )
    monkeypatch.setattr("data.version_tracker.__version__", "2.5.4")

    version_changed, previous_version, current_version = check_and_update_version()

    assert version_changed is False
    assert previous_version is None
    assert current_version == "2.5.4"
