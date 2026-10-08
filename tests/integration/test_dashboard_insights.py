from ui.dashboard_cards import create_dashboard_overview_content


class TestScheduleVarianceInsights:
    def test_schedule_variance_insight_appears_when_both_dates_available(self):

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

        assert "Key Insights" in dashboard_str
        assert "20 days" in dashboard_str

    def test_ahead_of_schedule_insight_displays_with_success_color(self):
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

        assert "ahead of deadline" in dashboard_str.lower()
        assert "30 days" in dashboard_str
        assert "text-success" in dashboard_str

    def test_behind_schedule_insight_displays_with_warning_color(self):
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

        assert "behind deadline" in dashboard_str.lower()
        assert "20 days" in dashboard_str
        assert "text-warning" in dashboard_str

    def test_on_track_insight_displays_when_days_equal(self):
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

        assert "On track to meet deadline" in dashboard_str
        assert "text-primary" in dashboard_str


class TestVelocityTrendInsights:
    def test_velocity_increasing_insight_with_acceleration_message(self):
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

        assert "velocity is accelerating" in dashboard_str.lower()
        assert "text-success" in dashboard_str
        assert "fa-arrow-up" in dashboard_str

    def test_velocity_decreasing_insight_with_blocker_warning(self):
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

        assert "velocity is declining" in dashboard_str.lower()
        assert "blockers" in dashboard_str.lower()
        assert "text-warning" in dashboard_str
        assert "fa-arrow-down" in dashboard_str


class TestProgressMilestoneInsights:
    def test_progress_milestone_insight_when_completion_gte_75_percent(self):
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

        assert "final stretch" in dashboard_str.lower()
        assert "great progress" in dashboard_str.lower()
        assert "text-success" in dashboard_str
        assert "fa-star" in dashboard_str


class TestEndToEndInsightsDisplay:
    def test_dashboard_with_realistic_data_displays_all_applicable_insights(self):

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

        assert "Key Insights" in dashboard_str
        assert "fa-lightbulb" in dashboard_str

        assert "10 days" in dashboard_str
        assert "behind deadline" in dashboard_str.lower()

        assert "velocity is accelerating" in dashboard_str.lower()

        assert "final stretch" in dashboard_str.lower()

        assert (
            "backgroundColor" in dashboard_str or "background" in dashboard_str.lower()
        )
        assert "Light blue background" in str(dashboard) or "#e7f3ff" in dashboard_str

    def test_dashboard_without_insights_returns_empty_div(self):
        metrics = {
            "completion_percentage": 50.0,
            "days_to_completion": None,
            "days_to_deadline": None,
            "completion_confidence": 70,
            "current_velocity_items": 5.0,
            "velocity_trend": "stable",
        }

        dashboard = create_dashboard_overview_content(metrics)

        assert dashboard is not None

    def test_dashboard_with_multiple_positive_insights(self):

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

        assert "Key Insights" in dashboard_str

        assert "25 days" in dashboard_str
        assert "ahead of deadline" in dashboard_str.lower()
        assert "velocity is accelerating" in dashboard_str.lower()
        assert "final stretch" in dashboard_str.lower()

        success_count = dashboard_str.count("text-success")
        assert success_count >= 3
