"""
Unit tests for version_tracker module.

Tests version change detection and database storage.
"""

import tempfile
from pathlib import Path

import pytest

from data.persistence.sqlite_backend import SQLiteBackend
from data.version_tracker import check_and_update_version


@pytest.fixture
def temp_db():
    """Create temporary database with schema for testing."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".db") as f:
        temp_path = Path(f.name)

    # Initialize schema
    from data.migration.schema_manager import initialize_schema

    initialize_schema(temp_path)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def backend_with_temp_db(temp_db):
    """Create backend instance using temporary database."""
    return SQLiteBackend(str(temp_db))


def test_check_and_update_version_first_run(temp_db, backend_with_temp_db, monkeypatch):
    """Test version tracking on first run (no previous version)."""
    # Patch get_backend to return our test backend
    monkeypatch.setattr(
        "data.version_tracker.get_backend", lambda: backend_with_temp_db
    )
    monkeypatch.setattr("data.version_tracker.__version__", "2.5.4")

    # First run - no previous version
    version_changed, previous_version, current_version = check_and_update_version()

    assert version_changed is False  # No change on first run
    assert previous_version is None
    assert current_version == "2.5.4"

    # Verify version was stored
    stored_version = backend_with_temp_db.get_app_state("last_run_version")
    assert stored_version == "2.5.4"


def test_check_and_update_version_no_change(temp_db, backend_with_temp_db, monkeypatch):
    """Test version tracking when version hasn't changed."""
    # Store initial version
    backend_with_temp_db.set_app_state("last_run_version", "2.5.4")

    # Patch get_backend to return our test backend
    monkeypatch.setattr(
        "data.version_tracker.get_backend", lambda: backend_with_temp_db
    )
    monkeypatch.setattr("data.version_tracker.__version__", "2.5.4")

    # Check version - should be no change
    version_changed, previous_version, current_version = check_and_update_version()

    assert version_changed is False
    assert previous_version == "2.5.4"
    assert current_version == "2.5.4"

    # Verify version still stored
    stored_version = backend_with_temp_db.get_app_state("last_run_version")
    assert stored_version == "2.5.4"


def test_check_and_update_version_changed(temp_db, backend_with_temp_db, monkeypatch):
    """Test version tracking when version has changed."""
    # Store old version
    backend_with_temp_db.set_app_state("last_run_version", "2.5.3")

    # Patch get_backend to return our test backend
    monkeypatch.setattr(
        "data.version_tracker.get_backend", lambda: backend_with_temp_db
    )
    monkeypatch.setattr("data.version_tracker.__version__", "2.5.4")

    # Check version - should detect change
    version_changed, previous_version, current_version = check_and_update_version()

    assert version_changed is True
    assert previous_version == "2.5.3"
    assert current_version == "2.5.4"

    # Verify new version is now stored
    stored_version = backend_with_temp_db.get_app_state("last_run_version")
    assert stored_version == "2.5.4"


def test_check_and_update_version_major_change(
    temp_db, backend_with_temp_db, monkeypatch
):
    """Test version tracking across major version change."""
    # Store old version
    backend_with_temp_db.set_app_state("last_run_version", "2.5.4")

    # Patch get_backend to return our test backend
    monkeypatch.setattr(
        "data.version_tracker.get_backend", lambda: backend_with_temp_db
    )
    monkeypatch.setattr("data.version_tracker.__version__", "3.0.0")

    # Check version - should detect change
    version_changed, previous_version, current_version = check_and_update_version()

    assert version_changed is True
    assert previous_version == "2.5.4"
    assert current_version == "3.0.0"

    # Verify new version is now stored
    stored_version = backend_with_temp_db.get_app_state("last_run_version")
    assert stored_version == "3.0.0"


def test_check_and_update_version_downgrade(temp_db, backend_with_temp_db, monkeypatch):
    """Test version tracking when version is downgraded (rollback scenario)."""
    # Store newer version
    backend_with_temp_db.set_app_state("last_run_version", "2.5.4")

    # Patch get_backend to return our test backend
    monkeypatch.setattr(
        "data.version_tracker.get_backend", lambda: backend_with_temp_db
    )
    monkeypatch.setattr("data.version_tracker.__version__", "2.5.3")

    # Check version - should still detect change
    version_changed, previous_version, current_version = check_and_update_version()

    assert version_changed is True
    assert previous_version == "2.5.4"
    assert current_version == "2.5.3"

    # Verify downgraded version is stored
    stored_version = backend_with_temp_db.get_app_state("last_run_version")
    assert stored_version == "2.5.3"


def test_check_and_update_version_error_handling(backend_with_temp_db, monkeypatch):
    """Test version tracking handles database errors gracefully."""

    # Mock get_app_state to raise an error
    def mock_get_app_state(key):
        raise RuntimeError("Database error")

    monkeypatch.setattr(backend_with_temp_db, "get_app_state", mock_get_app_state)
    monkeypatch.setattr(
        "data.version_tracker.get_backend", lambda: backend_with_temp_db
    )
    monkeypatch.setattr("data.version_tracker.__version__", "2.5.4")

    # Should not crash, returns safe defaults
    version_changed, previous_version, current_version = check_and_update_version()

    assert version_changed is False  # Safe default on error
    assert previous_version is None
    assert current_version == "2.5.4"
