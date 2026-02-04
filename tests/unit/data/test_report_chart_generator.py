"""Tests for report chart generation modules.

Tests the refactored chart generation modules that were split from chart_generator.py:
- chart_burndown.py
- chart_scope.py
- chart_bugs.py
- chart_flow.py
"""

from data.report.chart_generator import generate_chart_scripts
from data.report.chart_burndown import (
    generate_burndown_chart,
    generate_weekly_breakdown_chart,
)
from data.report.chart_scope import generate_scope_changes_chart
from data.report.chart_bugs import generate_bug_trends_chart
from data.report.chart_flow import generate_work_distribution_chart


class TestChartGeneratorOrchestration:
    """Test the main chart_generator orchestration."""

    def test_generate_chart_scripts_empty_sections(self):
        """Test with no sections returns empty list."""
        metrics = {}
        sections = []

        scripts = generate_chart_scripts(metrics, sections)

        assert scripts == []

    def test_generate_chart_scripts_burndown_section(self):
        """Test burndown section generates charts."""
        metrics = {
            "burndown": {
                "has_data": True,
                "historical_data": {
                    "dates": ["2026-01-01", "2026-01-15", "2026-01-31"],
                    "remaining_items": [30, 20, 10],
                    "remaining_points": [45, 30, 15],
                },
                "weekly_data": [
                    {
                        "date": "2026-01-07",
                        "created_items": 0,
                        "completed_items": 5,
                        "created_points": 0,
                        "completed_points": 8,
                    }
                ],
            },
            "dashboard": {
                "milestone": None,
                "forecast_date": None,
                "deadline": None,
                "show_points": False,
            },
        }
        sections = ["burndown"]

        scripts = generate_chart_scripts(metrics, sections)

        assert len(scripts) == 2  # Burndown chart + weekly breakdown
        assert all(isinstance(s, str) for s in scripts)
        assert all("Chart(" in s for s in scripts)

    def test_generate_chart_scripts_scope_section(self):
        """Test scope section generates scope changes chart."""
        metrics = {
            "scope": {
                "has_data": True,
            },
            "statistics": [
                {"date": "2026-01-10", "created_items": 1, "completed_items": 1},
                {"date": "2026-01-11", "created_items": 1, "completed_items": 0},
            ],
        }
        sections = ["burndown"]

        scripts = generate_chart_scripts(metrics, sections)

        assert len(scripts) >= 1
        assert any("scopeChangesChart" in s for s in scripts)

    def test_generate_chart_scripts_bugs_section(self):
        """Test bugs section generates bug trends chart."""
        metrics = {
            "bug_analysis": {
                "has_data": True,
                "weekly_stats": [
                    {
                        "week_start_date": "2026-01-01",
                        "bugs_created": 3,
                        "bugs_resolved": 2,
                    },
                    {
                        "week_start_date": "2026-01-08",
                        "bugs_created": 5,
                        "bugs_resolved": 4,
                    },
                ],
            }
        }
        sections = ["burndown"]

        scripts = generate_chart_scripts(metrics, sections)

        assert len(scripts) >= 1
        assert any("bugTrendsChart" in s for s in scripts)

    def test_generate_chart_scripts_flow_section(self):
        """Test flow section generates work distribution chart."""
        metrics = {
            "flow": {
                "has_data": True,
                "distribution_history": [
                    {
                        "week": "2026-W01",
                        "feature": 10,
                        "defect": 3,
                        "tech_debt": 2,
                        "risk": 1,
                        "total": 16,
                    }
                ],
            }
        }
        sections = ["flow"]

        scripts = generate_chart_scripts(metrics, sections)

        assert len(scripts) >= 1
        assert any("workDistributionChart" in s for s in scripts)

    def test_generate_chart_scripts_missing_data(self):
        """Test sections without data don't generate charts."""
        metrics = {
            "burndown": {"has_data": False},
            "scope": {"has_data": False},
            "bug_analysis": {"has_data": False},
            "flow": {"has_data": False},
        }
        sections = ["burndown", "flow"]

        scripts = generate_chart_scripts(metrics, sections)

        assert scripts == []


class TestBurndownCharts:
    """Test burndown chart generation."""

    def test_generate_burndown_chart_basic(self):
        """Test basic burndown chart generation."""
        burndown_metrics = {
            "historical_data": {
                "dates": ["2026-01-01", "2026-01-15", "2026-01-31"],
                "remaining_items": [30, 20, 10],
                "remaining_points": [45, 30, 15],
            }
        }

        script = generate_burndown_chart(burndown_metrics, "", "", "", False)

        assert "new Chart(" in script
        assert "burndownChart" in script
        assert "2026-01-01" in script
        assert "30" in script or "[30" in script
        assert "line" in script.lower()

    def test_generate_burndown_chart_with_points(self):
        """Test burndown chart with points enabled."""
        burndown_metrics = {
            "historical_data": {
                "dates": ["2026-01-01"],
                "remaining_items": [10],
                "remaining_points": [15],
            }
        }

        script = generate_burndown_chart(burndown_metrics, "", "", "", True)

        assert "Points" in script or "points" in script
        assert "15" in script or "[15" in script

    def test_generate_burndown_chart_with_annotations(self):
        """Test burndown chart with milestone, forecast, deadline."""
        burndown_metrics = {
            "historical_data": {
                "dates": ["2026-01-01", "2026-01-31"],
                "remaining_items": [30, 10],
                "remaining_points": [45, 15],
            }
        }
        milestone = "2026-01-15"
        forecast_date = "2026-02-10"
        deadline = "2026-02-28"

        script = generate_burndown_chart(
            burndown_metrics, milestone, forecast_date, deadline, False
        )

        assert "Milestone" in script
        assert "2026-01-15" in script
        assert "Forecast" in script
        assert "2026-02-10" in script
        assert "Deadline" in script
        assert "2026-02-28" in script

    def test_generate_weekly_breakdown_chart_basic(self):
        """Test weekly breakdown chart generation."""
        weekly_data = [
            {
                "date": "2026-01-07",
                "created_items": 3,
                "completed_items": 5,
                "created_points": 4,
                "completed_points": 8,
            },
            {
                "date": "2026-01-14",
                "created_items": 4,
                "completed_items": 7,
                "created_points": 6,
                "completed_points": 12,
            },
        ]

        script = generate_weekly_breakdown_chart(weekly_data, False)

        assert "new Chart(" in script
        assert "weeklyBreakdownChart" in script
        assert "2026-01-07" in script
        assert "2026-01-14" in script
        assert "bar" in script.lower()

    def test_generate_weekly_breakdown_chart_with_points(self):
        """Test weekly breakdown with points display."""
        weekly_data = [
            {
                "date": "2026-01-07",
                "created_items": 0,
                "completed_items": 5,
                "created_points": 0,
                "completed_points": 8,
            }
        ]

        script = generate_weekly_breakdown_chart(weekly_data, True)

        assert "Points" in script or "points" in script
        assert "8" in script or "[8" in script


class TestScopeChart:
    """Test scope changes chart generation."""

    def test_generate_scope_changes_chart_basic(self):
        """Test basic scope changes chart."""
        metrics = {
            "statistics": [
                {"date": "2026-01-10", "created_items": 1, "completed_items": 1},
                {"date": "2026-01-11", "created_items": 1, "completed_items": 1},
                {"date": "2026-01-12", "created_items": 1, "completed_items": 0},
            ]
        }

        script = generate_scope_changes_chart(metrics)

        assert "new Chart(" in script
        assert "scopeChangesChart" in script
        assert "bar" in script.lower()
        assert "Created" in script
        assert "Completed" in script

    def test_generate_scope_changes_chart_no_data(self):
        """Test scope chart with no items."""
        metrics = {"items": []}

        script = generate_scope_changes_chart(metrics)

        assert script == ""


class TestBugsChart:
    """Test bug trends chart generation."""

    def test_generate_bug_trends_chart_basic(self):
        """Test basic bug trends chart."""
        weekly_stats = [
            {"week_start_date": "2026-01-01", "bugs_created": 3, "bugs_resolved": 2},
            {"week_start_date": "2026-01-08", "bugs_created": 5, "bugs_resolved": 4},
            {"week_start_date": "2026-01-15", "bugs_created": 2, "bugs_resolved": 3},
        ]

        script = generate_bug_trends_chart(weekly_stats)

        assert "new Chart(" in script
        assert "bugTrendsChart" in script
        assert "2026-01-01" in script
        assert "line" in script.lower()
        assert "Created" in script or "created" in script
        assert "Closed" in script or "closed" in script

    def test_generate_bug_trends_chart_warning_backgrounds(self):
        """Test bug trends chart with consecutive negative weeks."""
        weekly_stats = [
            {"week_start_date": "2026-01-01", "bugs_created": 5, "bugs_resolved": 2},
            {"week_start_date": "2026-01-08", "bugs_created": 6, "bugs_resolved": 3},
            {"week_start_date": "2026-01-15", "bugs_created": 7, "bugs_resolved": 4},
            {"week_start_date": "2026-01-22", "bugs_created": 2, "bugs_resolved": 5},
        ]

        script = generate_bug_trends_chart(weekly_stats)

        # Should have warning backgrounds for 3+ consecutive negative weeks
        assert "annotation" in script.lower() or "box" in script.lower()

    def test_generate_bug_trends_chart_empty_data(self):
        """Test bug trends with empty data."""
        weekly_stats = []

        script = generate_bug_trends_chart(weekly_stats)

        # Should still generate valid empty chart
        assert "new Chart(" in script
        assert "bugTrendsChart" in script


class TestFlowChart:
    """Test flow metrics chart generation."""

    def test_generate_work_distribution_chart_basic(self):
        """Test basic work distribution chart."""
        flow_metrics = {
            "distribution_history": [
                {
                    "week": "2026-W01",
                    "feature": 10,
                    "defect": 3,
                    "tech_debt": 2,
                    "risk": 1,
                    "total": 16,
                },
                {
                    "week": "2026-W02",
                    "feature": 8,
                    "defect": 4,
                    "tech_debt": 3,
                    "risk": 2,
                    "total": 17,
                },
            ]
        }

        script = generate_work_distribution_chart(flow_metrics)

        assert "new Chart(" in script
        assert "workDistributionChart" in script
        assert "2026-W01" in script
        assert "bar" in script.lower()
        assert "stacked" in script.lower()
        assert "Feature" in script
        assert "Defect" in script

    def test_generate_work_distribution_chart_percentages(self):
        """Test work distribution shows percentages."""
        flow_metrics = {
            "distribution_history": [
                {
                    "week": "2026-W01",
                    "feature": 10,
                    "defect": 0,
                    "tech_debt": 0,
                    "risk": 0,
                    "total": 10,
                }
            ]
        }

        script = generate_work_distribution_chart(flow_metrics)

        # Should calculate percentages (100% features in this case)
        assert "100" in script or "percent" in script.lower() or "%" in script

    def test_generate_work_distribution_chart_empty_data(self):
        """Test work distribution with empty data."""
        flow_metrics = {"distribution_history": []}

        script = generate_work_distribution_chart(flow_metrics)

        assert script == ""


class TestChartScriptFormat:
    """Test that all generated scripts have correct format."""

    def test_all_scripts_are_iife(self):
        """Test all scripts are wrapped in IIFE (Immediately Invoked Function Expression)."""
        metrics = {
            "burndown": {
                "has_data": True,
                "historical_data": {
                    "dates": ["2026-01-01"],
                    "remaining_items": [10],
                    "remaining_points": [15],
                },
                "weekly_data": [
                    {
                        "date": "2026-01-07",
                        "created_items": 0,
                        "completed_items": 5,
                        "created_points": 0,
                        "completed_points": 8,
                    }
                ],
            },
            "scope": {
                "has_data": True,
            },
            "statistics": [
                {"date": "2026-01-10", "created_items": 1, "completed_items": 1}
            ],
            "bug_analysis": {
                "has_data": True,
                "weekly_stats": [
                    {
                        "week_start_date": "2026-01-01",
                        "bugs_created": 3,
                        "bugs_resolved": 2,
                    }
                ],
            },
            "flow": {
                "has_data": True,
                "distribution_history": [
                    {
                        "week": "2026-W01",
                        "feature": 10,
                        "defect": 3,
                        "tech_debt": 2,
                        "risk": 1,
                        "total": 16,
                    }
                ],
            },
            "dashboard": {"show_points": False},
        }
        sections = ["burndown", "flow"]

        scripts = generate_chart_scripts(metrics, sections)

        for script in scripts:
            # Check for IIFE pattern
            assert "(function()" in script or "(() =>" in script
            assert script.strip().endswith("();") or script.strip().endswith("})();")

    def test_all_scripts_check_element_exists(self):
        """Test all scripts check if DOM element exists before rendering."""
        metrics = {
            "burndown": {
                "has_data": True,
                "historical_data": {
                    "dates": ["2026-01-01"],
                    "remaining_items": [10],
                    "remaining_points": [15],
                },
            },
            "dashboard": {"show_points": False},
        }
        sections = ["burndown"]

        scripts = generate_chart_scripts(metrics, sections)

        for script in scripts:
            # Should have element existence check
            assert "getElementById" in script or "querySelector" in script
            assert "if (ctx)" in script or "if (canvas)" in script or "if (" in script
