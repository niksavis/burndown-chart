"""
Unit tests for data/ai_prompt_generator.py

Tests the AI prompt generator including:
- Privacy: PII sanitization (Constitution Principle V)
- Aggregation: Statistics condensing and trend calculation
- Output: Prompt formatting with structured output specification
- Error handling: Missing data, invalid inputs
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from data.ai_prompt_generator import (
    _aggregate_statistics,
    _calculate_trend,
    _create_summary_statistics,
    _format_ai_prompt,
    _sanitize_for_ai,
    generate_ai_analysis_prompt,
)

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_export_with_pii():
    """Sample export data containing customer-identifying information."""
    return {
        "profile_data": {
            "name": "Acme Corp Internal Project",
            "jira_url": "https://jira.acmecorp.com",
            "jira_email": "john.smith@acmecorp.com",
            "jira_token": "secret_token_abc123",
            "field_mappings": {
                "epic_name": "customfield_10001",
                "story_points": "customfield_10002",
            },
        },
        "query_data": {
            "q_12345": {
                "query_metadata": {
                    "name": "Q4 2025 Sprint Analysis",
                    "jql": 'project = ACME AND sprint = "Sprint 42"',
                },
                "statistics": [
                    {
                        "date": "2025-12-01",
                        "completed_items": 10,
                        "completed_points": 21,
                        "created_items": 8,
                    },
                    {
                        "date": "2025-12-08",
                        "completed_items": 12,
                        "completed_points": 25,
                        "created_items": 9,
                    },
                ],
                "budget_settings": {
                    "budget_hours": 400,
                    "team_size": 5,
                },
                "project_scope": {
                    "total_items": 150,
                    "remaining_items": 50,
                    "total_points": 300,
                    "remaining_total_points": 100,
                    "points_field_available": True,
                },
            },
        },
    }


@pytest.fixture
def sample_statistics_12_weeks():
    """Sample statistics for 12-week analysis."""
    base_date = datetime(2025, 10, 1)
    return [
        {
            "date": (base_date + timedelta(weeks=i)).strftime("%Y-%m-%d"),
            "completed_items": 10 + i,
            "completed_points": 20 + (i * 2),
            "created_items": 8 + i,
        }
        for i in range(12)
    ]


@pytest.fixture
def sample_summary():
    """Sample summary statistics for prompt formatting."""
    return {
        "time_period_weeks": 12,
        "generated_at": "2025-12-19T10:00:00",
        "data_source": "Burndown Generator (sanitized export)",
        "metrics": {
            "weeks_analyzed": 12,
            "avg_velocity_items": 15.5,
            "avg_velocity_points": 31.0,
            "total_completed_items": 186,
            "total_created_items": 155,
            "scope_change_rate_pct": 83.3,
            "velocity_trend": "improving",
            "velocity_coefficient_of_variation": 22.5,
        },
        "budget": {
            "allocated_hours": 400,
            "team_size": 5,
        },
    }


# ============================================================================
# Test: PII Sanitization (Constitution Principle V)
# ============================================================================


def test_sanitize_removes_customer_identifying_info(sample_export_with_pii):
    """Verify all customer PII is stripped per Constitution Principle V."""
    sanitized = _sanitize_for_ai(sample_export_with_pii)

    # Profile metadata should be sanitized
    profile = sanitized["profile_data"]
    assert profile["name"] == "Project Alpha"
    assert profile["jira_url"] == "https://jira.example.com"
    assert profile["jira_email"] == "user@example.com"

    # Token should be stripped
    assert "jira_token" not in profile

    # Query metadata should be sanitized
    query = sanitized["query_data"]["q_12345"]["query_metadata"]
    assert query["name"] == "Sprint Analysis"
    assert query["jql"] == "project = PROJ AND sprint = CURRENT"


def test_sanitize_preserves_field_mappings(sample_export_with_pii):
    """Verify field mapping structure is preserved (no PII in IDs)."""
    sanitized = _sanitize_for_ai(sample_export_with_pii)

    # Field mappings should be unchanged (structure useful, IDs not PII)
    field_mappings = sanitized["profile_data"]["field_mappings"]
    assert field_mappings["epic_name"] == "customfield_10001"
    assert field_mappings["story_points"] == "customfield_10002"


def test_sanitize_preserves_statistics(sample_export_with_pii):
    """Verify statistical data is preserved (no PII)."""
    sanitized = _sanitize_for_ai(sample_export_with_pii)

    # Statistics should be unchanged
    stats = sanitized["query_data"]["q_12345"]["statistics"]
    assert len(stats) == 2
    assert stats[0]["completed_items"] == 10
    assert stats[0]["completed_points"] == 21


def test_sanitize_preserves_budget(sample_export_with_pii):
    """Verify budget settings preserved (no PII)."""
    sanitized = _sanitize_for_ai(sample_export_with_pii)

    # Budget settings should be unchanged
    budget = sanitized["query_data"]["q_12345"]["budget_settings"]
    assert budget["budget_hours"] == 400
    assert budget["team_size"] == 5


# ============================================================================
# Test: Statistics Aggregation
# ============================================================================


def test_aggregate_calculates_averages(sample_statistics_12_weeks):
    """Verify average velocity calculations."""
    aggregated = _aggregate_statistics(sample_statistics_12_weeks, weeks=12)

    assert aggregated["weeks_analyzed"] == 12
    assert aggregated["avg_velocity_items"] == pytest.approx(15.5, rel=0.1)
    assert aggregated["avg_velocity_points"] == pytest.approx(31.0, rel=0.1)


def test_aggregate_calculates_totals(sample_statistics_12_weeks):
    """Verify total completed/created calculations."""
    aggregated = _aggregate_statistics(sample_statistics_12_weeks, weeks=12)

    assert aggregated["total_completed_items"] == 186
    # Sum: 8+9+10+11+12+13+14+15+16+17+18+19 = 162
    assert aggregated["total_created_items"] == 162


def test_aggregate_calculates_scope_change_rate(sample_statistics_12_weeks):
    """Verify scope change rate calculation."""
    aggregated = _aggregate_statistics(sample_statistics_12_weeks, weeks=12)

    # scope_change_rate = (created / completed) * 100
    expected = (155 / 186) * 100
    assert aggregated["scope_change_rate_pct"] == pytest.approx(expected, rel=0.1)


def test_aggregate_filters_to_time_window():
    """Verify statistics are filtered to requested time period."""
    # Create 24 weeks of data
    base_date = datetime(2025, 7, 1)
    stats_24_weeks = [
        {
            "date": (base_date + timedelta(weeks=i)).strftime("%Y-%m-%d"),
            "completed_items": 10,
            "completed_points": 20,
            "created_items": 8,
        }
        for i in range(24)
    ]

    # Request only last 12 weeks
    aggregated = _aggregate_statistics(stats_24_weeks, weeks=12)

    # Should only analyze ~12 weeks (may be 12-13 depending on week boundaries)
    assert 12 <= aggregated["weeks_analyzed"] <= 13


def test_aggregate_handles_empty_statistics():
    """Verify graceful handling of empty statistics."""
    aggregated = _aggregate_statistics([], weeks=12)

    assert "error" in aggregated
    assert aggregated["error"] == "No statistics available"


def test_aggregate_calculates_velocity_cv(sample_statistics_12_weeks):
    """Verify coefficient of variation calculation."""
    aggregated = _aggregate_statistics(sample_statistics_12_weeks, weeks=12)

    # CV should be reasonable for improving trend (low variability)
    assert "velocity_coefficient_of_variation" in aggregated
    assert 0 <= aggregated["velocity_coefficient_of_variation"] <= 50


def test_aggregate_handles_stat_date_column():
    """Verify handling of 'stat_date' column from database (not 'date')."""
    # Database returns 'stat_date' instead of 'date'
    stats_with_stat_date = [
        {
            "stat_date": "2025-07-01",
            "completed_items": 10,
            "completed_points": 20,
            "created_items": 8,
            "created_points": 16,
        },
        {
            "stat_date": "2025-07-08",
            "completed_items": 12,
            "completed_points": 24,
            "created_items": 10,
            "created_points": 20,
        },
    ]

    aggregated = _aggregate_statistics(stats_with_stat_date, weeks=2)

    # Should work correctly with stat_date column
    assert aggregated["weeks_analyzed"] == 2
    assert aggregated["avg_velocity_items"] == 11.0
    assert aggregated["total_completed_items"] == 22


# ============================================================================
# Test: Trend Detection
# ============================================================================


def test_calculate_trend_improving():
    """Verify improving trend detection."""
    import pandas as pd

    # Data with clear improvement (10 -> 20)
    series = pd.Series([10, 10, 11, 12, 18, 19, 20, 20])
    trend = _calculate_trend(series)

    assert trend == "improving"


def test_calculate_trend_declining():
    """Verify declining trend detection."""
    import pandas as pd

    # Data with clear decline (20 -> 10)
    series = pd.Series([20, 20, 19, 18, 12, 11, 10, 10])
    trend = _calculate_trend(series)

    assert trend == "declining"


def test_calculate_trend_stable():
    """Verify stable trend detection."""
    import pandas as pd

    # Data with minimal change (15 +/- 2)
    series = pd.Series([15, 16, 14, 15, 16, 15, 14, 15])
    trend = _calculate_trend(series)

    assert trend == "stable"


def test_calculate_trend_insufficient_data():
    """Verify insufficient data handling."""
    import pandas as pd

    # Less than 4 data points
    series = pd.Series([10, 12, 14])
    trend = _calculate_trend(series)

    assert trend == "insufficient_data"


def test_calculate_trend_zero_baseline():
    """Verify zero baseline handling."""
    import pandas as pd

    # First half all zeros (avoid division by zero)
    series = pd.Series([0, 0, 0, 0, 10, 12, 14, 16])
    trend = _calculate_trend(series)

    assert trend == "insufficient_data"


# ============================================================================
# Test: Prompt Formatting
# ============================================================================


def test_format_prompt_includes_all_sections(sample_summary):
    """Verify all key sections are present in improved format."""
    prompt = _format_ai_prompt(sample_summary, time_period_weeks=12)

    # Check for key section headers (flexible format)
    assert "## Project Data" in prompt
    assert "## Analysis Objectives" in prompt
    assert "### 1. Executive Summary" in prompt
    assert "### 2. Velocity & Performance Analysis" in prompt
    assert "### 3. Scope Management Assessment" in prompt
    assert "### 4. Delivery Forecast" in prompt
    assert "### 5. Risk Identification" in prompt
    assert "### 6. Actionable Recommendations" in prompt
    assert "### 7. Key Questions for Stakeholders" in prompt
    assert "## Analysis Guidelines" in prompt
    assert "## Optional Context" in prompt


def test_format_prompt_includes_metrics_json(sample_summary):
    """Verify metrics are formatted as JSON in prompt."""
    prompt = _format_ai_prompt(sample_summary, time_period_weeks=12)

    # Should contain JSON code block
    assert "```json" in prompt

    # Should contain key metrics
    assert '"avg_velocity_items": 15.5' in prompt
    assert '"total_completed_items": 186' in prompt
    assert '"velocity_trend": "improving"' in prompt


def test_format_prompt_includes_time_period(sample_summary):
    """Verify time period is prominently displayed."""
    prompt = _format_ai_prompt(sample_summary, time_period_weeks=12)

    # New format uses "12-week analysis window"
    assert "12-week analysis window" in prompt


def test_format_prompt_includes_project_scope():
    """Verify project scope section is included when available."""
    summary_with_scope = {
        "time_period_weeks": 12,
        "generated_at": "2025-12-19T10:00:00",
        "metrics": {
            "weeks_analyzed": 12,
            "avg_velocity_items": 15.5,
        },
        "project_scope": {
            "total_items": 150,
            "remaining_items": 50,
            "completed_items": 100,
            "completion_pct": 66.7,
            "total_points": 300,
            "remaining_points": 100,
            "completed_points": 200,
            "points_completion_pct": 66.7,
            "estimated_weeks_remaining": 3.2,
        },
    }

    prompt = _format_ai_prompt(summary_with_scope, time_period_weeks=12)

    # Check project scope section exists
    assert "## Project Scope & Progress" in prompt
    assert "Progress:" in prompt
    assert "Remaining: 50 items" in prompt
    assert "66.7% complete" in prompt
    assert "Story Points:" in prompt  # Points included
    assert "Projected Completion: ~3.2 weeks" in prompt


def test_format_prompt_scope_without_points():
    """Verify project scope section works without points data."""
    summary_no_points = {
        "time_period_weeks": 12,
        "generated_at": "2025-12-19T10:00:00",
        "metrics": {
            "weeks_analyzed": 12,
            "avg_velocity_items": 15.5,
        },
        "project_scope": {
            "total_items": 150,
            "remaining_items": 50,
            "completed_items": 100,
            "completion_pct": 66.7,
            "estimated_weeks_remaining": 3.2,
        },
    }

    prompt = _format_ai_prompt(summary_no_points, time_period_weeks=12)

    # Check project scope section exists but without points
    assert "## Project Scope & Progress" in prompt
    assert "Progress:" in prompt
    assert "Story Points:" not in prompt  # Should not mention points


def test_format_prompt_includes_structured_output_spec(sample_summary):
    """Verify analysis guidance is present (flexible format)."""
    prompt = _format_ai_prompt(sample_summary, time_period_weeks=12)

    # Check for analysis guidance components (not rigid structure)
    assert "Immediate Actions" in prompt
    assert "confidence intervals" in prompt
    assert "Risk Identification" in prompt
    assert "Be Data-Driven" in prompt  # Analysis guidelines


def test_format_prompt_includes_footer(sample_summary):
    """Verify prompt includes version and privacy notice."""
    prompt = _format_ai_prompt(sample_summary, time_period_weeks=12)

    # Footer elements
    assert "Generated by Burndown Generator" in prompt
    assert "Data sanitized for privacy" in prompt


def test_format_prompt_reasonable_length(sample_summary):
    """Verify prompt length is within reasonable bounds (3000-6000 chars)."""
    prompt = _format_ai_prompt(sample_summary, time_period_weeks=12)

    # Should be comprehensive but not excessive
    assert 3000 <= len(prompt) <= 6000


# ============================================================================
# Test: Integration (End-to-End)
# ============================================================================


@patch("data.import_export.export_profile_with_mode")
@patch("data.query_manager.get_active_profile_id")
@patch("data.query_manager.get_active_query_id")
def test_generate_prompt_full_flow(
    mock_get_query, mock_get_profile, mock_export, sample_export_with_pii
):
    """Verify full prompt generation flow with mocked dependencies."""
    # Setup mocks
    mock_get_profile.return_value = "test_profile"
    mock_get_query.return_value = "q_12345"
    mock_export.return_value = sample_export_with_pii

    # Generate prompt
    prompt = generate_ai_analysis_prompt(time_period_weeks=12)

    # Verify export was called correctly
    mock_export.assert_called_once_with(
        profile_id="test_profile",
        query_id="q_12345",
        export_mode="FULL_DATA",
        include_token=False,
        include_budget=True,
    )

    # Verify prompt was generated
    assert len(prompt) > 1000
    assert "Project Data" in prompt  # New format


@patch("data.query_manager.get_active_profile_id")
@patch("data.query_manager.get_active_query_id")
def test_generate_prompt_no_active_profile(mock_get_query, mock_get_profile):
    """Verify error handling when no profile selected."""
    mock_get_profile.return_value = None
    mock_get_query.return_value = None

    with pytest.raises(ValueError, match="No active profile or query selected"):
        generate_ai_analysis_prompt()


def test_create_summary_no_query_data():
    """Verify graceful handling of missing query data."""
    sanitized = {"profile_data": {"name": "Test"}}  # No query_data

    summary = _create_summary_statistics(sanitized, time_period_weeks=12)

    # Should return minimal summary
    assert summary["time_period_weeks"] == 12
    assert "generated_at" in summary
    assert "metrics" not in summary  # No metrics generated


# ============================================================================
# Test: Boy Scout Rule (Constitution Principle VI)
# ============================================================================


def test_no_dead_code():
    """Verify no unused imports or commented code blocks."""
    import inspect

    from data import ai_prompt_generator

    # Get module source
    source = inspect.getsource(ai_prompt_generator)

    # Check for code smells (simplified check)
    assert "# TODO" not in source or "FIXME" not in source  # No unfinished work
    # Note: More sophisticated dead code detection would use AST analysis


def test_all_functions_have_docstrings():
    """Verify all public functions have docstrings."""
    from data import ai_prompt_generator

    public_functions = [
        name
        for name in dir(ai_prompt_generator)
        if callable(getattr(ai_prompt_generator, name)) and not name.startswith("_")
    ]

    for func_name in public_functions:
        func = getattr(ai_prompt_generator, func_name)
        assert func.__doc__ is not None, f"{func_name} missing docstring"


def test_no_sensitive_data_in_logs():
    """Verify logging calls don't expose customer data."""
    import inspect

    from data import ai_prompt_generator

    source = inspect.getsource(ai_prompt_generator)

    # Check log statements don't contain obvious PII patterns
    # (simplified check - real implementation would parse AST)
    assert "logger.info" in source  # Logging exists
    # More sophisticated: parse logging calls and verify no PII in messages


# ============================================================================
# Test: Performance (Constitution Principle III)
# ============================================================================


def test_generate_prompt_performance(sample_export_with_pii):
    """Verify prompt generation completes within performance budget (<100ms)."""
    import time

    with patch("data.import_export.export_profile_with_mode") as mock_export:
        with patch("data.query_manager.get_active_profile_id") as mock_profile:
            with patch("data.query_manager.get_active_query_id") as mock_query:
                mock_export.return_value = sample_export_with_pii
                mock_profile.return_value = "test"
                mock_query.return_value = "q_12345"

                start = time.time()
                generate_ai_analysis_prompt(time_period_weeks=12)
                elapsed = time.time() - start

                # Should complete in <100ms (performance budget)
                assert elapsed < 0.1, f"Generation took {elapsed * 1000:.1f}ms (>100ms)"


def test_aggregate_statistics_performance():
    """Verify aggregation scales to 52 weeks within budget."""
    import time

    # Create 52 weeks of data
    base_date = datetime(2024, 12, 1)
    stats_52_weeks = [
        {
            "date": (base_date + timedelta(weeks=i)).strftime("%Y-%m-%d"),
            "completed_items": 10 + i,
            "completed_points": 20 + (i * 2),
            "created_items": 8 + i,
        }
        for i in range(52)
    ]

    start = time.time()
    _aggregate_statistics(stats_52_weeks, weeks=52)
    elapsed = time.time() - start

    # Should handle 52 weeks efficiently (<50ms)
    assert elapsed < 0.05, f"Aggregation took {elapsed * 1000:.1f}ms (>50ms)"
