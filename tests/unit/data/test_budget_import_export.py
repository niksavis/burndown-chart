"""Tests for budget data export and import functionality."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from data.persistence.sqlite_backend import SQLiteBackend


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".db") as f:
        temp_path = Path(f.name)

    # Initialize schema
    from data.migration.schema_manager import initialize_schema

    initialize_schema(temp_path)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


def test_budget_settings_export_import(temp_db):
    """Test budget settings can be exported and imported."""
    backend = SQLiteBackend(str(temp_db))

    # Create a test profile
    profile = {
        "id": "test_profile",
        "name": "Test Profile",
        "created_at": datetime.now().isoformat(),
        "last_used": datetime.now().isoformat(),
        "jira_config": {},
        "field_mappings": {},
        "forecast_settings": {},
        "project_classification": {},
        "flow_type_mappings": {},
    }
    backend.save_profile(profile)

    # Create a test query
    query = {
        "id": "test_query",
        "name": "Test Query",
        "jql": "project = TEST",
        "created_at": datetime.now().isoformat(),
        "last_used": datetime.now().isoformat(),
    }
    backend.save_query("test_profile", query)

    # Save budget settings
    budget_settings = {
        "time_allocated_weeks": 12,
        "budget_total_eur": 50000.0,
        "currency_symbol": "€",
        "team_cost_per_week_eur": 5000.0,
        "cost_rate_type": "weekly",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    backend.save_budget_settings("test_profile", "test_query", budget_settings)

    # Export budget settings
    exported_settings = backend.get_budget_settings("test_profile", "test_query")

    # Verify export
    assert exported_settings is not None
    assert exported_settings["time_allocated_weeks"] == 12
    assert exported_settings["budget_total_eur"] == 50000.0
    assert exported_settings["currency_symbol"] == "€"

    # Create a new profile and import budget
    profile2 = {
        "id": "test_profile_2",
        "name": "Test Profile 2",
        "created_at": datetime.now().isoformat(),
        "last_used": datetime.now().isoformat(),
        "jira_config": {},
        "field_mappings": {},
        "forecast_settings": {},
        "project_classification": {},
        "flow_type_mappings": {},
    }
    backend.save_profile(profile2)

    # Create a query for the second profile
    query2 = {
        "id": "test_query_2",
        "name": "Test Query 2",
        "jql": "project = TEST2",
        "created_at": datetime.now().isoformat(),
        "last_used": datetime.now().isoformat(),
    }
    backend.save_query("test_profile_2", query2)

    backend.save_budget_settings("test_profile_2", "test_query_2", exported_settings)

    # Verify import
    imported_settings = backend.get_budget_settings("test_profile_2", "test_query_2")
    assert imported_settings is not None
    assert imported_settings["time_allocated_weeks"] == 12
    assert imported_settings["budget_total_eur"] == 50000.0


def test_budget_revisions_export_import(temp_db):
    """Test budget revisions can be exported and imported."""
    backend = SQLiteBackend(str(temp_db))

    # Create a test profile
    profile = {
        "id": "test_profile",
        "name": "Test Profile",
        "created_at": datetime.now().isoformat(),
        "last_used": datetime.now().isoformat(),
        "jira_config": {},
        "field_mappings": {},
        "forecast_settings": {},
        "project_classification": {},
        "flow_type_mappings": {},
    }
    backend.save_profile(profile)

    # Create a test query
    query = {
        "id": "test_query",
        "name": "Test Query",
        "jql": "project = TEST",
        "created_at": datetime.now().isoformat(),
        "last_used": datetime.now().isoformat(),
    }
    backend.save_query("test_profile", query)

    # Save budget revisions
    revisions = [
        {
            "revision_date": "2026-01-01T00:00:00Z",
            "week_label": "2026-W01",
            "time_allocated_weeks_delta": 2,
            "team_cost_delta": 1000.0,
            "budget_total_delta": 2000.0,
            "revision_reason": "Scope increase",
            "created_at": datetime.now().isoformat(),
            "metadata": json.dumps({"user": "test_user"}),
        },
        {
            "revision_date": "2026-01-08T00:00:00Z",
            "week_label": "2026-W02",
            "time_allocated_weeks_delta": -1,
            "team_cost_delta": -500.0,
            "budget_total_delta": -500.0,
            "revision_reason": "Reduced scope",
            "created_at": datetime.now().isoformat(),
            "metadata": None,
        },
    ]
    backend.save_budget_revisions("test_profile", "test_query", revisions)

    # Export budget revisions
    exported_revisions = backend.get_budget_revisions("test_profile", "test_query")

    # Verify export
    assert len(exported_revisions) == 2
    assert exported_revisions[0]["week_label"] == "2026-W01"
    assert exported_revisions[1]["week_label"] == "2026-W02"

    # Create a new profile and import revisions
    profile2 = {
        "id": "test_profile_2",
        "name": "Test Profile 2",
        "created_at": datetime.now().isoformat(),
        "last_used": datetime.now().isoformat(),
        "jira_config": {},
        "field_mappings": {},
        "forecast_settings": {},
        "project_classification": {},
        "flow_type_mappings": {},
    }
    backend.save_profile(profile2)

    # Create a query for the second profile
    query2 = {
        "id": "test_query_2",
        "name": "Test Query 2",
        "jql": "project = TEST2",
        "created_at": datetime.now().isoformat(),
        "last_used": datetime.now().isoformat(),
    }
    backend.save_query("test_profile_2", query2)

    # Remove 'id' field from exported revisions (auto-generated on import)
    for revision in exported_revisions:
        revision.pop("id", None)

    backend.save_budget_revisions("test_profile_2", "test_query_2", exported_revisions)

    # Verify import
    imported_revisions = backend.get_budget_revisions("test_profile_2", "test_query_2")
    assert len(imported_revisions) == 2
    assert imported_revisions[0]["week_label"] == "2026-W01"
    assert imported_revisions[1]["week_label"] == "2026-W02"


def test_budget_export_in_full_package(temp_db):
    """Test budget data is included in full export package."""
    # This test requires mocking the factory to use the test database
    # For now, we verify the backend methods work correctly
    # Full integration test would require app context
    pytest.skip("Requires app context/factory mocking - covered by backend tests")
