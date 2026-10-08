import dash_bootstrap_components as dbc
from dash import html

from ui.dashboard_cards import (
    _calculate_health_score,
    _create_key_insights,
    _get_health_color_and_label,
    create_dashboard_forecast_card,
    create_dashboard_overview_content,
    create_dashboard_pert_card,
    create_dashboard_remaining_card,
    create_dashboard_velocity_card,
)


class TestHealthScore:
    def test_progress_component_normal(self):
        metrics = {
            "completion_percentage": 68.0,
            "days_to_completion": 30,
            "days_to_deadline": 45,
            "velocity_trend": "stable",
            "completion_confidence": 75,
        }

        health = _calculate_health_score(metrics)

        assert 40 <= health <= 100
        assert isinstance(health, int)

    def test_schedule_component_on_track(self):
        metrics = {
            "completion_percentage": 50.0,
            "days_to_completion": 30,
            "days_to_deadline": 45,
            "velocity_trend": "stable",
            "completion_confidence": 75,
        }

        health = _calculate_health_score(metrics)

        assert 40 <= health <= 100
        assert isinstance(health, int)

    def test_schedule_component_behind(self):
        metrics = {
            "completion_percentage": 50.0,
            "days_to_completion": 50,
            "days_to_deadline": 45,
            "velocity_trend": "stable",
            "completion_confidence": 75,
        }

        health = _calculate_health_score(metrics)

        assert 30 <= health <= 100
        assert isinstance(health, int)

    def test_velocity_component_increasing(self):
        metrics = {
            "completion_percentage": 50.0,
            "trend_direction": "improving",
            "velocity_cv": 20,
            "schedule_variance_days": 0,
        }

        health_improving = _calculate_health_score(metrics)

        metrics["trend_direction"] = "stable"
        health_stable = _calculate_health_score(metrics)

        assert health_improving >= health_stable

    def test_velocity_component_decreasing(self):
        metrics = {
            "completion_percentage": 50.0,
            "days_to_completion": 30,
            "days_to_deadline": 45,
            "trend_direction": "declining",
            "velocity_cv": 20,
        }

        health_decreasing = _calculate_health_score(metrics)

        metrics["trend_direction"] = "improving"
        health_improving = _calculate_health_score(metrics)

        assert health_improving >= health_decreasing

    def test_confidence_component_high(self):
        metrics = {
            "completion_percentage": 50.0,
            "velocity_cv": 15,
            "trend_direction": "stable",
            "schedule_variance_days": 0,
        }

        health = _calculate_health_score(metrics)

        assert 0 <= health <= 100
        assert isinstance(health, int)

    def test_health_score_composite_excellent(self):
        metrics = {
            "completion_percentage": 85.0,
            "velocity_cv": 10,
            "schedule_variance_days": 0,
            "scope_change_rate": 2,
            "trend_direction": "improving",
        }

        health = _calculate_health_score(metrics)

        assert health >= 50
        assert health <= 100

    def test_health_score_composite_fair(self):
        metrics = {
            "velocity_cv": 35,
            "schedule_variance_days": 25,
            "scope_change_rate": 20,
            "trend_direction": "stable",
            "recent_velocity_change": 0,
        }

        health = _calculate_health_score(metrics)

        assert 40 <= health < 60

    def test_health_score_composite_needs_attention(self):
        metrics = {
            "velocity_cv": 60,
            "schedule_variance_days": 50,
            "scope_change_rate": 35,
            "trend_direction": "declining",
            "recent_velocity_change": -25,
        }

        health = _calculate_health_score(metrics)

        assert 0 <= health < 60


class TestHealthColorLabel:
    def test_excellent_tier(self):
        color, label = _get_health_color_and_label(85)

        assert color == "#198754"
        assert label == "Good"

    def test_good_tier(self):
        color, label = _get_health_color_and_label(70)

        assert color == "#198754"
        assert label == "Good"

    def test_fair_tier(self):
        color, label = _get_health_color_and_label(50)

        assert color == "#ffc107"
        assert label == "Caution"

    def test_needs_attention_tier(self):
        color, label = _get_health_color_and_label(30)

        assert color == "#fd7e14"
        assert label == "At Risk"


class TestKeyInsights:
    def test_schedule_insight_ahead(self):
        metrics = {
            "days_to_completion": 30,
            "days_to_deadline": 45,
            "velocity_trend": "stable",
            "completion_percentage": 50.0,
        }

        insights_div = _create_key_insights(metrics)

        insights_text = str(insights_div)
        assert "ahead" in insights_text.lower()

    def test_schedule_insight_behind(self):
        metrics = {
            "days_to_completion": 50,
            "days_to_deadline": 40,
            "velocity_trend": "stable",
            "completion_percentage": 50.0,
        }

        insights_div = _create_key_insights(metrics)

        insights_text = str(insights_div)
        assert "behind" in insights_text.lower()

    def test_velocity_insight_increasing(self):
        metrics = {
            "days_to_completion": 30,
            "days_to_deadline": 45,
            "velocity_trend": "increasing",
            "completion_percentage": 50.0,
        }

        insights_div = _create_key_insights(metrics)

        insights_text = str(insights_div)
        assert "velocity" in insights_text.lower() or "trend" in insights_text.lower()

    def test_velocity_insight_decreasing(self):
        metrics = {
            "days_to_completion": 30,
            "days_to_deadline": 45,
            "velocity_trend": "decreasing",
            "completion_percentage": 50.0,
        }

        insights_div = _create_key_insights(metrics)

        insights_text = str(insights_div)
        assert "velocity" in insights_text.lower() or "trend" in insights_text.lower()

    def test_insights_returns_div(self):
        metrics = {
            "days_to_completion": 30,
            "days_to_deadline": 45,
            "velocity_trend": "stable",
            "completion_percentage": 50.0,
        }

        insights = _create_key_insights(metrics)

        assert isinstance(insights, html.Div)


class TestForecastCard:
    def test_card_structure(self):
        metrics = {
            "completion_percentage": 68.0,
            "days_to_completion": 30,
            "days_to_deadline": 45,
        }

        card = create_dashboard_forecast_card(metrics)

        assert isinstance(card, dbc.Card)
        assert card.children is not None

    def test_card_displays_completion(self):
        metrics = {
            "completion_percentage": 68.0,
            "days_to_completion": 30,
            "days_to_deadline": 45,
        }

        card = create_dashboard_forecast_card(metrics)

        card_text = str(card)
        assert "30" in card_text

    def test_card_displays_forecast_date(self):
        metrics = {
            "completion_percentage": 50.0,
            "forecast_completion_date": "2025-12-31",
            "days_to_completion": 30,
        }

        card = create_dashboard_forecast_card(metrics)

        card_text = str(card)
        assert "2025" in card_text or "forecast" in card_text.lower()


class TestVelocityCard:
    def test_card_structure(self):
        metrics = {
            "items_per_week": 5.2,
            "points_per_week": 26.0,
            "velocity_trend": "stable",
        }

        card = create_dashboard_velocity_card(metrics)

        assert isinstance(card, dbc.Card)
        assert card.children is not None

    def test_card_displays_items_per_week(self):
        metrics = {
            "items_per_week": 5.2,
            "points_per_week": 26.0,
            "velocity_trend": "stable",
        }

        card = create_dashboard_velocity_card(metrics)

        card_text = str(card)
        assert "5.2" in card_text or "items" in card_text.lower()

    def test_card_displays_velocity_trend(self):
        metrics = {
            "items_per_week": 5.2,
            "points_per_week": 26.0,
            "velocity_trend": "increasing",
        }

        card = create_dashboard_velocity_card(metrics)

        card_text = str(card)
        assert "accelerating" in card_text.lower() or "increasing" in card_text.lower()


class TestRemainingCard:
    def test_card_structure(self):
        metrics = {"remaining_items": 32, "remaining_points": 160}

        card = create_dashboard_remaining_card(metrics)

        assert isinstance(card, dbc.Card)
        assert card.children is not None

    def test_card_displays_remaining_items(self):
        metrics = {"remaining_items": 32, "remaining_points": 160}

        card = create_dashboard_remaining_card(metrics)

        card_text = str(card)
        assert "32" in card_text


class TestPertCard:
    def test_card_structure(self):
        metrics = {
            "optimistic_date": "2025-11-15",
            "likely_date": "2025-12-01",
            "pessimistic_date": "2025-12-31",
        }

        card = create_dashboard_pert_card(metrics)

        assert isinstance(card, dbc.Card)
        assert card.children is not None

    def test_card_displays_pert_dates(self):
        metrics = {
            "optimistic_date": "2025-11-15",
            "likely_date": "2025-12-01",
            "pessimistic_date": "2025-12-31",
            "days_to_deadline": 50,
        }

        card = create_dashboard_pert_card(metrics)

        card_text = str(card)
        assert "50" in card_text or "days" in card_text.lower()


class TestOverviewContent:
    def test_overview_returns_div(self):
        metrics = {
            "completion_percentage": 68.0,
            "items_per_week": 5.2,
            "remaining_items": 32,
            "velocity_trend": "stable",
        }

        overview = create_dashboard_overview_content(metrics)

        assert isinstance(overview, html.Div)

    def test_overview_includes_health_indicator(self):
        metrics = {
            "completion_percentage": 68.0,
            "days_to_completion": 30,
            "days_to_deadline": 45,
            "velocity_trend": "stable",
            "completion_confidence": 75,
        }

        overview = create_dashboard_overview_content(metrics)

        overview_text = str(overview)
        assert "health" in overview_text.lower() or "status" in overview_text.lower()

    def test_overview_responsive_layout(self):
        metrics = {
            "completion_percentage": 68.0,
            "items_per_week": 5.2,
            "remaining_items": 32,
        }

        overview = create_dashboard_overview_content(metrics)

        overview_text = str(overview)
        assert (
            "Row" in overview_text
            or "Col" in overview_text
            or "row" in overview_text.lower()
        )
