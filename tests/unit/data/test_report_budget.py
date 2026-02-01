"""Tests for budget metrics in report generation."""

import pytest
import tempfile
from datetime import datetime
from pathlib import Path


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


def test_budget_metrics_calculation_with_data(temp_db):
    """Test budget metrics calculation when budget is configured."""
    from data.report.helpers import (
        calculate_budget_metrics as _calculate_budget_metrics,
    )
    from data.persistence.sqlite_backend import SQLiteBackend
    from unittest.mock import patch

    backend = SQLiteBackend(str(temp_db))

    # Create profile
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
        "time_allocated_weeks": 52,
        "team_cost_per_week_eur": 5000.0,
        "budget_total_eur": 260000.0,
        "currency_symbol": "€",
        "cost_rate_type": "weekly",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    backend.save_budget_settings("test_profile", "test_query", budget_settings)

    # Calculate metrics with mocked backend
    with patch("data.persistence.factory.get_backend", return_value=backend):
        with patch(
            "data.persistence.load_unified_project_data",
            return_value={"statistics": [], "project_scope": {}, "settings": {}},
        ):
            metrics = _calculate_budget_metrics("test_profile", "test_query", 12)

    # Verify structure
    assert metrics["has_data"] is True
    assert metrics["time_allocated_weeks"] == 52
    assert metrics["cost_per_week"] == 5000.0
    assert metrics["budget_total"] == 260000.0
    assert metrics["currency_symbol"] == "€"
    assert "consumed_amount" in metrics
    assert "consumed_percentage" in metrics
    assert "remaining_amount" in metrics
    assert "runway_weeks" in metrics


def test_budget_metrics_calculation_no_budget(temp_db):
    """Test budget metrics calculation when no budget is configured."""
    from data.report.helpers import (
        calculate_budget_metrics as _calculate_budget_metrics,
    )
    from data.persistence.sqlite_backend import SQLiteBackend

    backend = SQLiteBackend(str(temp_db))

    # Create profile without budget
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

    # Calculate metrics
    metrics = _calculate_budget_metrics("test_profile", "test_query", 12)

    # Verify empty response
    assert metrics["has_data"] is False


def test_budget_in_report_sections(temp_database):
    """Test that budget section is included in report when requested."""
    from data.report.generator import calculate_all_metrics as _calculate_all_metrics

    # Mock report data
    report_data = {
        "profile_id": "test_profile",
        "all_statistics": [],
        "statistics": [],
        "project_scope": {"remaining_items": 100, "remaining_total_points": 500},
        "settings": {"show_points": False},
        "weeks_count": 12,
        "snapshots": [],
        "jira_issues": [],
    }

    # Calculate with budget section
    sections = ["budget"]
    metrics = _calculate_all_metrics(report_data, sections, 12)

    # Verify budget is in metrics
    assert "budget" in metrics


def test_budget_size_estimate():
    """Test that budget is included in report size estimation."""
    from callbacks.report_generation import update_report_size_estimate

    # Test with budget
    sections_with_budget = ["burndown", "budget"]
    result_with = update_report_size_estimate(sections_with_budget)

    # Test without budget
    sections_without = ["burndown"]
    result_without = update_report_size_estimate(sections_without)

    # Budget should add to size estimate
    assert result_with != result_without
    assert "MB" in result_with
    assert "MB" in result_without
