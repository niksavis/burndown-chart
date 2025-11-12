"""
Integration tests for Dashboard Insights Display.

Tests that key insights section displays correctly for different scenarios:
- Schedule variance (ahead, behind, on-track)
- Velocity trends (increasing, decreasing, stable)
- Progress milestones (≥75% complete)

These tests verify insights are integrated into the dashboard layout and
rendered with correct styling, colors, and messaging.

Related Tasks:
- T086: Create integration test file structure
- T087-T093: Test individual insight scenarios
- T094: End-to-end test with realistic data
"""

from ui.dashboard_cards import create_dashboard_overview_content


class TestScheduleVarianceInsights:
    """Test schedule variance insights (ahead/behind/on-track)."""

    def test_schedule_variance_insight_appears_when_both_dates_available(self):
        """T087: Verify schedule variance insight appears when both days_to_completion and days_to_deadline available."""
        metrics = {
            "completion_percentage": 50.0,
            "days_to_completion": 80,
            "days_to_deadline": 100,
            "completion_confidence": 75,
            "current_velocity_items": 5.0,
            "velocity_trend": "stable",
        }

        dashboard = create_dashboard_overview_content(metrics)
        dashboard_str = str(dashboard)

        # Should contain insights section with schedule variance
        assert "Key Insights" in dashboard_str
        # Should show ahead of schedule (100 - 80 = 20 days)
        assert "20 days" in dashboard_str

    def test_ahead_of_schedule_insight_displays_with_success_color(self):
        """T088: Verify ahead-of-schedule insight displays with success color and day count."""
        metrics = {
            "completion_percentage": 60.0,
            "days_to_completion": 70,
            "days_to_deadline": 100,
            "completion_confidence": 80,
            "current_velocity_items": 5.5,
            "velocity_trend": "stable",
        }

        dashboard = create_dashboard_overview_content(metrics)
        dashboard_str = str(dashboard)

        # Should show ahead message with success color
        assert "ahead of deadline" in dashboard_str.lower()
        assert "30 days" in dashboard_str  # 100 - 70
        assert "text-success" in dashboard_str  # Green color for ahead

    def test_behind_schedule_insight_displays_with_warning_color(self):
        """T089: Verify behind-schedule insight displays with warning color and day count."""
        metrics = {
            "completion_percentage": 40.0,
            "days_to_completion": 120,
            "days_to_deadline": 100,
            "completion_confidence": 60,
            "current_velocity_items": 4.0,
            "velocity_trend": "stable",
        }

        dashboard = create_dashboard_overview_content(metrics)
        dashboard_str = str(dashboard)

        # Should show behind message with warning color
        assert "behind deadline" in dashboard_str.lower()
        assert "20 days" in dashboard_str  # 120 - 100
        assert "text-warning" in dashboard_str  # Warning color for behind

    def test_on_track_insight_displays_when_days_equal(self):
        """T090: Verify on-track insight displays when completion and deadline days are equal."""
        metrics = {
            "completion_percentage": 55.0,
            "days_to_completion": 90,
            "days_to_deadline": 90,
            "completion_confidence": 75,
            "current_velocity_items": 5.0,
            "velocity_trend": "stable",
        }

        dashboard = create_dashboard_overview_content(metrics)
        dashboard_str = str(dashboard)

        # Should show on-track message
        assert "On track to meet deadline" in dashboard_str
        assert "text-primary" in dashboard_str  # Primary color for on-track


class TestVelocityTrendInsights:
    """Test velocity trend insights (increasing/decreasing)."""

    def test_velocity_increasing_insight_with_acceleration_message(self):
        """T091: Verify velocity increasing insight displays with acceleration messaging."""
        metrics = {
            "completion_percentage": 50.0,
            "days_to_completion": 80,
            "days_to_deadline": 100,
            "completion_confidence": 75,
            "current_velocity_items": 6.0,
            "velocity_trend": "increasing",
        }

        dashboard = create_dashboard_overview_content(metrics)
        dashboard_str = str(dashboard)

        # Should show velocity increasing message
        assert "velocity is accelerating" in dashboard_str.lower()
        assert "text-success" in dashboard_str  # Green for positive trend
        assert "fa-arrow-up" in dashboard_str  # Up arrow icon

    def test_velocity_decreasing_insight_with_blocker_warning(self):
        """T092: Verify velocity decreasing insight displays with blocker warning."""
        metrics = {
            "completion_percentage": 45.0,
            "days_to_completion": 100,
            "days_to_deadline": 110,
            "completion_confidence": 65,
            "current_velocity_items": 4.0,
            "velocity_trend": "decreasing",
        }

        dashboard = create_dashboard_overview_content(metrics)
        dashboard_str = str(dashboard)

        # Should show velocity declining message with blocker warning
        assert "velocity is declining" in dashboard_str.lower()
        assert "blockers" in dashboard_str.lower()
        assert "text-warning" in dashboard_str  # Warning color
        assert "fa-arrow-down" in dashboard_str  # Down arrow icon


class TestProgressMilestoneInsights:
    """Test progress milestone insights (≥75% complete)."""

    def test_progress_milestone_insight_when_completion_gte_75_percent(self):
        """T093: Verify progress milestone insight appears when completion ≥75%."""
        metrics = {
            "completion_percentage": 80.0,
            "days_to_completion": 30,
            "days_to_deadline": 45,
            "completion_confidence": 85,
            "current_velocity_items": 7.0,
            "velocity_trend": "stable",
        }

        dashboard = create_dashboard_overview_content(metrics)
        dashboard_str = str(dashboard)

        # Should show final stretch message
        assert "final stretch" in dashboard_str.lower()
        assert "great progress" in dashboard_str.lower()
        assert "text-success" in dashboard_str  # Success color
        assert "fa-star" in dashboard_str  # Star icon for milestone


class TestEndToEndInsightsDisplay:
    """End-to-end test with realistic project data."""

    def test_dashboard_with_realistic_data_displays_all_applicable_insights(self):
        """T094: Load dashboard with realistic project data, verify all applicable insights display.

        Scenario: Project is behind schedule, velocity increasing, and in final stretch.
        Should display 3 insights:
        1. Behind schedule warning
        2. Velocity accelerating (positive)
        3. Final stretch milestone
        """
        metrics = {
            "completion_percentage": 78.0,
            "days_to_completion": 50,
            "days_to_deadline": 40,
            "completion_confidence": 70,
            "current_velocity_items": 6.5,
            "velocity_trend": "increasing",
        }

        dashboard = create_dashboard_overview_content(metrics)
        dashboard_str = str(dashboard)

        # Should have Key Insights section
        assert "Key Insights" in dashboard_str
        assert "fa-lightbulb" in dashboard_str  # Insights icon

        # Insight 1: Behind schedule (50 - 40 = 10 days)
        assert "10 days" in dashboard_str
        assert "behind deadline" in dashboard_str.lower()

        # Insight 2: Velocity increasing
        assert "velocity is accelerating" in dashboard_str.lower()

        # Insight 3: Final stretch (78% >= 75%)
        assert "final stretch" in dashboard_str.lower()

        # Verify styling elements
        assert (
            "backgroundColor" in dashboard_str or "background" in dashboard_str.lower()
        )
        assert "Light blue background" in str(dashboard) or "#e7f3ff" in dashboard_str

    def test_dashboard_without_insights_returns_empty_div(self):
        """Test that dashboard with no applicable insights returns empty div (no crash)."""
        metrics = {
            "completion_percentage": 50.0,
            "days_to_completion": None,  # No completion forecast
            "days_to_deadline": None,  # No deadline
            "completion_confidence": 70,
            "current_velocity_items": 5.0,
            "velocity_trend": "stable",  # Stable velocity (no insight)
        }

        dashboard = create_dashboard_overview_content(metrics)

        # Should not crash, but insights section should be minimal or absent
        # (no schedule comparison, no velocity trend insight, <75% complete)
        assert dashboard is not None

    def test_dashboard_with_multiple_positive_insights(self):
        """Test dashboard displays multiple positive insights correctly.

        Scenario: Ahead of schedule, velocity increasing, final stretch.
        All green/success insights.
        """
        metrics = {
            "completion_percentage": 85.0,
            "days_to_completion": 25,
            "days_to_deadline": 50,
            "completion_confidence": 90,
            "current_velocity_items": 8.0,
            "velocity_trend": "increasing",
        }

        dashboard = create_dashboard_overview_content(metrics)
        dashboard_str = str(dashboard)

        # Should have Key Insights section
        assert "Key Insights" in dashboard_str

        # All three insights should be present
        assert "25 days" in dashboard_str  # 50 - 25 days ahead
        assert "ahead of deadline" in dashboard_str.lower()
        assert "velocity is accelerating" in dashboard_str.lower()
        assert "final stretch" in dashboard_str.lower()

        # Multiple success color elements (all positive insights)
        success_count = dashboard_str.count("text-success")
        assert success_count >= 3  # At least 3 success-colored insights
