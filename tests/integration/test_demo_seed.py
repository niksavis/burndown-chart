import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

import pytest

from data.demo.config import SCENARIOS
from tests.fixtures.demo_workspace import run_demo_seed


def test_demo_contains_all_scenarios_and_real_calculated_snapshots(
    generated_demo: Path,
) -> None:
    with (
        closing(sqlite3.connect(generated_demo / "burndown.db")) as connection,
        connection,
    ):
        profiles = connection.execute("SELECT id FROM profiles").fetchall()
        assert {row[0] for row in profiles} == {
            f"demo-{scenario}" for scenario in SCENARIOS
        }
        weeks = connection.execute(
            "SELECT week_label FROM project_statistics WHERE profile_id = ? ORDER BY stat_date",
            ("demo-complete",),
        ).fetchall()
        assert [row[0] for row in weeks] == [
            "2025-W50",
            "2025-W51",
            "2025-W52",
            "2026-W01",
            "2026-W02",
            "2026-W03",
            "2026-W04",
            "2026-W05",
        ]
        points = connection.execute(
            "SELECT SUM(points) FROM jira_issues "
            "WHERE profile_id = ? AND issue_type != ? AND project_key = ?",
            ("demo-complete", "Epic", "DEMO"),
        ).fetchone()
        assert points == (96.0,)
        metrics = connection.execute(
            "SELECT DISTINCT metric_name FROM metrics_data_points WHERE profile_id = ?",
            ("demo-complete",),
        ).fetchall()
        assert {row[0] for row in metrics} >= {
            "flow_velocity",
            "flow_time",
            "flow_efficiency",
            "dora_deployment_frequency",
            "dora_lead_time",
            "dora_change_failure_rate",
            "dora_mttr",
        }
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute(
            "SELECT value FROM app_state WHERE key = ?", ("active_profile_id",)
        ).fetchone() == ("demo-complete",)


def test_repeated_launch_preserves_developer_edits_and_revision_counts(
    generated_demo: Path,
) -> None:
    with (
        closing(sqlite3.connect(generated_demo / "burndown.db")) as connection,
        connection,
    ):
        connection.execute(
            "INSERT INTO app_state VALUES (?, ?)", ("developer_edit", "preserved")
        )
        before = connection.execute("SELECT COUNT(*) FROM budget_revisions").fetchone()
    run_demo_seed(generated_demo, generated_demo / "repeat.log")
    with (
        closing(sqlite3.connect(generated_demo / "burndown.db")) as connection,
        connection,
    ):
        assert connection.execute(
            "SELECT value FROM app_state WHERE key = ?", ("developer_edit",)
        ).fetchone() == ("preserved",)
        assert (
            connection.execute("SELECT COUNT(*) FROM budget_revisions").fetchone()
            == before
        )


@pytest.mark.parametrize("existing_file", [False, True])
def test_empty_development_workspace_can_start_without_synthetic_profiles(
    existing_file: bool,
) -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        workspace = root / "demo"
        workspace.mkdir()
        if existing_file:
            sqlite3.connect(workspace / "burndown.db").close()
        run_demo_seed(workspace, root / "empty.log", empty=True)
        with (
            closing(sqlite3.connect(workspace / "burndown.db")) as connection,
            connection,
        ):
            assert connection.execute("SELECT COUNT(*) FROM profiles").fetchone() == (
                0,
            )
            assert (
                connection.execute(
                    "SELECT value FROM app_state WHERE key = ?", ("demo_seed_version",)
                ).fetchone()
                is not None
            )
