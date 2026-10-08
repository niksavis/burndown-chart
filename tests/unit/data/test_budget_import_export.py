import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from data.persistence.sqlite_backend import SQLiteBackend


@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".db") as f:
        temp_path = Path(f.name)

    from data.migration.schema_manager import initialize_schema

    initialize_schema(temp_path)

    yield temp_path

    if temp_path.exists():
        temp_path.unlink()


def test_budget_settings_export_import(temp_db):
    backend = SQLiteBackend(str(temp_db))

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

    query = {
        "id": "test_query",
        "name": "Test Query",
        "jql": "project = TEST",
        "created_at": datetime.now().isoformat(),
        "last_used": datetime.now().isoformat(),
    }
    backend.save_query("test_profile", query)

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

    exported_settings = backend.get_budget_settings("test_profile", "test_query")

    assert exported_settings is not None
    assert exported_settings["time_allocated_weeks"] == 12
    assert exported_settings["budget_total_eur"] == 50000.0
    assert exported_settings["currency_symbol"] == "€"

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

    query2 = {
        "id": "test_query_2",
        "name": "Test Query 2",
        "jql": "project = TEST2",
        "created_at": datetime.now().isoformat(),
        "last_used": datetime.now().isoformat(),
    }
    backend.save_query("test_profile_2", query2)

    backend.save_budget_settings("test_profile_2", "test_query_2", exported_settings)

    imported_settings = backend.get_budget_settings("test_profile_2", "test_query_2")
    assert imported_settings is not None
    assert imported_settings["time_allocated_weeks"] == 12
    assert imported_settings["budget_total_eur"] == 50000.0


def test_budget_revisions_export_import(temp_db):
    backend = SQLiteBackend(str(temp_db))

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

    query = {
        "id": "test_query",
        "name": "Test Query",
        "jql": "project = TEST",
        "created_at": datetime.now().isoformat(),
        "last_used": datetime.now().isoformat(),
    }
    backend.save_query("test_profile", query)

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

    exported_revisions = backend.get_budget_revisions("test_profile", "test_query")

    assert len(exported_revisions) == 2
    assert exported_revisions[0]["week_label"] == "2026-W01"
    assert exported_revisions[1]["week_label"] == "2026-W02"

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

    query2 = {
        "id": "test_query_2",
        "name": "Test Query 2",
        "jql": "project = TEST2",
        "created_at": datetime.now().isoformat(),
        "last_used": datetime.now().isoformat(),
    }
    backend.save_query("test_profile_2", query2)

    for revision in exported_revisions:
        revision.pop("id", None)

    backend.save_budget_revisions("test_profile_2", "test_query_2", exported_revisions)

    imported_revisions = backend.get_budget_revisions("test_profile_2", "test_query_2")
    assert len(imported_revisions) == 2
    assert imported_revisions[0]["week_label"] == "2026-W01"
    assert imported_revisions[1]["week_label"] == "2026-W02"
