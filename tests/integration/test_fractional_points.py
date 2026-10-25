from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from data.jira.data_transformer import jira_to_csv_format
from data.jira.field_utils import extract_story_points_value
from data.jira.scope_calculator import calculate_jira_project_scope
from data.report.helpers import (
    calculate_historical_burndown,
    calculate_weekly_breakdown,
)
from data.scope_metrics import calculate_total_project_scope


@pytest.mark.parametrize(
    "value", [2.5, "2.5", {"value": "2.5"}, {"count": 2.5}, {"total": 2.5}]
)
@pytest.mark.parametrize("nested", [False, True])
def test_fractional_scope_preserves_field_representations(
    value: Any, nested: bool
) -> None:
    fields = {"customfield_10001": value}
    if nested:
        fields = {"custom_fields": fields}
    issues = [dict(fields, status="Done", status_category="done")]
    scope = calculate_jira_project_scope(issues, "customfield_10001")
    assert scope["total_points"] == 2.5
    assert scope["completed_points"] == 2.5
    assert scope["total_items"] == 1


def test_fractional_scope_estimation_and_status_totals() -> None:
    issues = [
        {"status": "Done", "status_category": "done", "customfield_10001": 2.5},
        {"status": "To Do", "status_category": "new", "customfield_10001": 3.5},
        {"status": "To Do", "status_category": "new", "customfield_10001": 0.5},
    ]
    scope = calculate_jira_project_scope(issues, "customfield_10001")
    assert (
        scope["total_points"],
        scope["completed_points"],
        scope["remaining_points"],
    ) == (6.5, 2.5, 4.0)
    assert scope["estimated_points"] == 4.0
    assert scope["remaining_total_points"] == 4.0
    assert scope["status_breakdown"]["Done"]["points"] == 2.5
    assert (
        scope["total_items"],
        scope["completed_items"],
        scope["remaining_items"],
    ) == (3, 1, 2)


def test_fractional_report_totals_and_historical_marks() -> None:
    statistics = [
        {
            "date": "2026-01-05",
            "created_items": 3,
            "completed_items": 1,
            "created_points": 6.5,
            "completed_points": 2.5,
        }
    ]
    weekly = calculate_weekly_breakdown(statistics)
    assert weekly[0]["created_points"] == 6.5
    assert weekly[0]["completed_points"] == 2.5
    history = calculate_historical_burndown(
        statistics, {"remaining_items": 2, "remaining_total_points": 4.0}
    )
    assert history["remaining_points"] == [6.5]
    assert history["remaining_items"] == [3]
    assert calculate_total_project_scope(pd.DataFrame(statistics), 2, 4.0) == {
        "total_items": 3,
        "total_points": 6.5,
    }


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -0.5, True, "invalid"])
def test_invalid_points_are_refused_by_name(value: Any) -> None:
    with pytest.raises(ValueError, match="customfield_10001"):
        extract_story_points_value(value, "customfield_10001")


def test_fractional_weekly_extraction() -> None:
    issues = [
        {
            "fields": {
                "created": "2026-01-05",
                "resolutiondate": "2026-01-06",
                "customfield_10001": value,
            }
        }
        for value in [2.5, "3.5", {"value": 0.5}]
    ]
    statistics = jira_to_csv_format(issues, {"story_points_field": "customfield_10001"})
    assert statistics[0]["created_points"] == 6.5
    assert statistics[0]["completed_points"] == 6.5
    assert statistics[0]["completed_items"] == 3


@pytest.mark.parametrize("cleaner", ["statistics", "import"])
def test_fractional_statistics_preparation(cleaner: str) -> None:
    from data.persistence.adapters.sample_data import read_and_clean_data
    from data.processing_statistics import process_statistics_data

    frame = pd.DataFrame(
        [
            {
                "date": "2026-01-05",
                "completed_items": 1,
                "created_items": 3,
                "completed_points": 2.5,
                "created_points": 6.5,
            }
        ]
    )
    cleaned = (
        process_statistics_data(frame, {})
        if cleaner == "statistics"
        else read_and_clean_data(frame)
    )
    assert cleaned["completed_points"].tolist() == [2.5]
    assert cleaned["created_points"].tolist() == [6.5]
    assert cleaned["completed_items"].tolist() == [1]


def test_fractional_scope_growth_has_valid_week_labels() -> None:
    from data.scope_metrics import calculate_weekly_scope_growth

    frame = pd.DataFrame(
        [
            {
                "date": "2026-01-05",
                "completed_items": 1,
                "created_items": 3,
                "completed_points": 2.5,
                "created_points": 6.5,
            }
        ]
    )
    growth = calculate_weekly_scope_growth(frame)
    assert growth["week_label"].tolist() == ["2026-W02"]
    assert growth["points_growth"].tolist() == [4.0]


@pytest.mark.parametrize("value", [0, 3, None, ""])
def test_zero_integer_and_missing_point_controls(value: Any) -> None:
    assert extract_story_points_value(value, "customfield_10001") == (
        3.0 if value == 3 else 0.0
    )


def test_fractional_demo_persistence_matches_source_population(
    generated_demo: Path,
) -> None:
    import json
    import sqlite3
    from contextlib import closing

    with closing(sqlite3.connect(generated_demo / "burndown.db")) as connection:
        source = connection.execute(
            "SELECT SUM(points) FROM jira_issues WHERE profile_id = ?",
            ("demo-fractional-points",),
        ).fetchone()
        assert source == (6.5,)
        row = connection.execute(
            "SELECT scope_data FROM project_scope WHERE profile_id = ?",
            ("demo-fractional-points",),
        ).fetchone()
        scope = json.loads(row[0])
        assert scope["total_points"] == 6.5
        assert scope["completed_points"] == 6.5
        statistics = connection.execute(
            "SELECT completed_points, created_points FROM project_statistics WHERE profile_id = ?",
            ("demo-fractional-points",),
        ).fetchall()
        assert statistics == [(6.5, 6.5)]


@pytest.mark.parametrize("wrapper", ["value", "count", "total", "points", "votes"])
def test_fractional_issue_storage_accepts_the_same_formats(
    generated_demo: Path, wrapper: str
) -> None:
    from data.demo.config import AS_OF
    from data.demo.issues import scenario_issues
    from data.persistence.sqlite.backend import SQLiteBackend

    backend = SQLiteBackend(str(generated_demo / "burndown.db"))
    issues = scenario_issues("fractional-points")
    for issue, value in zip(issues, [2.5, 3.5, 0.5], strict=True):
        issue["fields"]["customfield_10001"] = {wrapper: str(value)}
    backend.save_issues_batch(
        "demo-fractional-points", "main", "synthetic-demo", issues, AS_OF
    )
    assert backend.renormalize_points("demo-fractional-points", "main") == 3
    stored = backend.get_issues("demo-fractional-points", "main")
    assert sorted(issue["points"] for issue in stored) == [0.5, 2.5, 3.5]


@pytest.mark.parametrize("value", [None, "", {"value": None}, []])
def test_missing_points_remain_unestimated(value: Any) -> None:
    issues = [
        {"status": "Done", "status_category": "done", "customfield_10001": 2.5},
        {"status": "To Do", "status_category": "new", "customfield_10001": value},
    ]
    scope = calculate_jira_project_scope(issues, "customfield_10001")
    assert scope["estimated_items"] == 0
    assert scope["remaining_total_points"] == 2.5


def test_explicit_zero_points_remain_estimated() -> None:
    scope = calculate_jira_project_scope(
        [{"status": "To Do", "status_category": "new", "customfield_10001": 0}],
        "customfield_10001",
    )
    assert scope["estimated_items"] == 1
    assert scope["remaining_total_points"] == 0


def test_fractional_forecast_uses_unrounded_scope_and_delivery() -> None:
    from data.processing_rates import calculate_rates

    frame = pd.DataFrame(
        {
            "date": ["2026-01-05", "2026-01-12"],
            "completed_items": [1, 1],
            "completed_points": [2.625, 2.625],
        }
    )
    rates = calculate_rates(frame, 2, 5.25, 1)
    assert rates[3] == pytest.approx(14.0)


def test_fractional_legacy_import_is_preserved(monkeypatch) -> None:
    from data.persistence.adapters import jira_config

    statistics = [
        {
            "date": "2026-01-05",
            "completed_items": 1,
            "created_items": 3,
            "completed_points": 2.5,
            "created_points": 6.5,
        }
    ]
    saved = []
    monkeypatch.setattr(jira_config, "load_statistics", lambda: (statistics, True))
    monkeypatch.setattr(
        jira_config,
        "load_project_data",
        lambda: {"total_items": 3, "total_points": 6.5},
    )
    monkeypatch.setattr(jira_config, "save_unified_project_data", saved.append)
    result = jira_config.migrate_csv_to_json()
    assert result["statistics"][0]["velocity_points"] == 2.5
    assert result["statistics"][0]["completed_points"] == 2.5
    assert result["statistics"][0]["created_points"] == 6.5
    assert saved == [result]


def test_fractional_forecast_annotations_match_encoded_values() -> None:
    import plotly.graph_objects as go

    from visualization.forecast_chart_layout import add_metrics_annotations

    metrics = {
        "deadline": "2026-02-26",
        "days_to_deadline": 28,
        "total_scope_items": 3,
        "total_scope_points": 6.5,
        "completed_items": 1,
        "completed_points": 2.5,
        "items_percent_complete": 33.3,
        "points_percent_complete": 38.5,
        "total_items": 2,
        "total_points": 4.0,
        "pert_time_items": 14,
        "pert_time_points": 14,
        "avg_weekly_items": 1,
        "avg_weekly_points": 2.0,
    }
    figure = add_metrics_annotations(go.Figure(), metrics)
    text = [annotation.text for annotation in figure.layout.annotations]
    assert "<b>Scope Points:</b> 6.5" in text
    assert "<b>Completed Points:</b> 2.5 (38.5%)" in text
    assert "<b>Remaining Points:</b> 4.0" in text
    assert "<b>Scope Items:</b> 3" in text
