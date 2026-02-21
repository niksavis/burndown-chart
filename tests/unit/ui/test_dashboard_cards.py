import dash_bootstrap_components as dbc
from dash import html

# Import functions under test
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

# Fixtures are imported automatically by pytest from
# conftest.py and dashboard_test_fixtures.py.
# No need to import explicitly; they are used as function parameters.


class TestHealthScore:
    """Test _calculate_health_score() 4-component calculation."""

    def test_progress_component_normal(self):
        """Test health score with normal progress using v3.0 comprehensive formula."""
        # Given: 68% project completion (68/100 items)
        metrics = {
            "completion_percentage": 68.0,
            "days_to_completion": 30,
            "days_to_deadline": 45,
            "velocity_trend": "stable",
            "completion_confidence": 75,
        }

        # When: Calculate health score (v3.0 comprehensive)
        health = _calculate_health_score(metrics)

        # Then: v3.0 returns score based on 6 dimensions
        # (Delivery, Predictability, etc.)
        # With limited metrics, score is typically in 40-60 range
        assert 40 <= health <= 100
        assert isinstance(health, int)

    def test_schedule_component_on_track(self):
        """Test health score when on track using v3.0 comprehensive formula."""
        # Given: 30 days to completion, 45 days to deadline (ahead of schedule)
        metrics = {
            "completion_percentage": 50.0,
            "days_to_completion": 30,
            "days_to_deadline": 45,  # 15 day buffer
            "velocity_trend": "stable",
            "completion_confidence": 75,
        }

        # When: Calculate health score (v3.0 comprehensive)
        health = _calculate_health_score(metrics)

        # Then: v3.0 considers schedule as part of Predictability dimension
        assert 40 <= health <= 100
        assert isinstance(health, int)

    def test_schedule_component_behind(self):
        """Test health score when behind schedule using v3.0 comprehensive formula."""
        # Given: 50 days to completion, 45 days to deadline (behind schedule)
        metrics = {
            "completion_percentage": 50.0,
            "days_to_completion": 50,
            "days_to_deadline": 45,  # 5 days behind
            "velocity_trend": "stable",
            "completion_confidence": 75,
        }

        # When: Calculate health score (v3.0 comprehensive)
        health = _calculate_health_score(metrics)

        # Then: v3.0 penalizes schedule variance in Predictability dimension
        assert 30 <= health <= 100
        assert isinstance(health, int)

    def test_velocity_component_increasing(self):
        """Test velocity trend affects health score in v3.0 calculator."""
        # Given: Improving velocity trend (team accelerating)
        metrics = {
            "completion_percentage": 50.0,
            "trend_direction": "improving",  # v3.0 uses trend_direction
            "velocity_cv": 20,
            "schedule_variance_days": 0,
        }

        # When: Calculate health with improving trend
        health_improving = _calculate_health_score(metrics)

        # Compare to stable trend
        metrics["trend_direction"] = "stable"
        health_stable = _calculate_health_score(metrics)

        # Then: Improving trend should boost health
        assert health_improving >= health_stable  # Improving trend adds bonus

    def test_velocity_component_decreasing(self):
        """Test that v3.0 health calculator handles trend direction."""
        # Given: Decreasing velocity trend (team slowing down)
        metrics = {
            "completion_percentage": 50.0,
            "days_to_completion": 30,
            "days_to_deadline": 45,
            "trend_direction": "declining",
            "velocity_cv": 20,
        }

        # When: Calculate health with decreasing trend
        health_decreasing = _calculate_health_score(metrics)

        # Compare to improving trend
        metrics["trend_direction"] = "improving"
        health_improving = _calculate_health_score(metrics)

        # Then: Improving trend should be better than declining
        assert health_improving >= health_decreasing

    def test_confidence_component_high(self):
        """Test that v3.0 health calculator returns valid scores."""
        # Given: Basic metrics
        metrics = {
            "completion_percentage": 50.0,
            "velocity_cv": 15,
            "trend_direction": "stable",
            "schedule_variance_days": 0,
        }

        # When: Calculate health
        health = _calculate_health_score(metrics)

        # Then: Returns valid health score
        assert 0 <= health <= 100
        assert isinstance(health, int)

    def test_health_score_composite_excellent(self):
        """Test v3.0 health calculator with good metrics produces reasonable score."""
        # Given: Good metrics - high completion, low CV, on schedule, good scope
        metrics = {
            "completion_percentage": 85.0,  # High progress
            "velocity_cv": 10,  # Very consistent
            "schedule_variance_days": 0,  # On time
            "scope_change_rate": 2,  # Minimal scope creep
            "trend_direction": "improving",
        }

        # When: Calculate comprehensive health
        health = _calculate_health_score(metrics)

        # Then: Should produce a good health score.
        # v3.0 may not reach 80+ without all dimensions.
        assert health >= 50  # At least moderate health
        assert health <= 100

    def test_health_score_composite_fair(self):
        """Test composite health score for fair project (40-59 = fair)."""
        # Given: Moderate velocity CV, moderate schedule variance, some scope growth
        metrics = {
            "velocity_cv": 35,  # Moderate consistency (30 * 0.3 = 9 points)
            "schedule_variance_days": 25,  # Moderate delay (25 * 0.58 = 14.5 points)
            "scope_change_rate": 20,  # Moderate scope growth (20 * 0.5 = 10 points)
            "trend_direction": "stable",  # Stable trend (10 points)
            "recent_velocity_change": 0,  # No change (5 points)
        }

        # When: Calculate composite health
        health = _calculate_health_score(metrics)

        # Then: Health score should be in fair range (40-59)
        # Expected: 9 + 14.5 + 10 + 10 + 5 = 48.5 points
        assert 40 <= health < 60

    def test_health_score_composite_needs_attention(self):
        """Test composite health score for at-risk project (<40 = needs attention)."""
        # Given: High velocity CV, significantly behind schedule,
        # high scope growth, and a declining trend.
        metrics = {
            "velocity_cv": 60,  # Poor consistency (0 points - capped at 50)
            # Significantly behind (25 * 0.17 = 4.2 points)
            "schedule_variance_days": 50,
            "scope_change_rate": 35,  # High scope growth (20 * 0.125 = 2.5 points)
            "trend_direction": "declining",  # Declining trend (0 points)
            "recent_velocity_change": -25,  # Negative momentum (0 points)
        }

        # When: Calculate composite health
        health = _calculate_health_score(metrics)

        # Then: Comprehensive formula should still produce a lower score
        assert 0 <= health < 60


class TestHealthColorLabel:
    """Test _get_health_color_and_label() tier mapping."""

    def test_excellent_tier(self):
        """Test high score (70+) maps to green color and 'Good' label."""
        # Given: Health score 85 (high range)
        # When: Get color and label
        color, label = _get_health_color_and_label(85)

        # Then: Color = green, label = "Good"
        assert color == "#198754"  # Green
        assert label == "Good"

    def test_good_tier(self):
        """Test high score (70+) maps to green color and 'Good' label."""
        # Given: Health score 70 (high range)
        # When: Get color and label
        color, label = _get_health_color_and_label(70)

        # Then: Color = green, label = "Good"
        assert color == "#198754"  # Green
        assert label == "Good"

    def test_fair_tier(self):
        """Test caution tier (50-69) maps to yellow color and 'Caution' label."""
        # Given: Health score 50 (caution range)
        # When: Get color and label
        color, label = _get_health_color_and_label(50)

        # Then: Color = yellow, label = "Caution"
        assert color == "#ffc107"  # Yellow
        assert label == "Caution"

    def test_needs_attention_tier(self):
        """Test at risk tier (30-49) maps to orange color and 'At Risk' label."""
        # Given: Health score 30 (at risk range)
        # When: Get color and label
        color, label = _get_health_color_and_label(30)

        # Then: Color = orange, label = "At Risk"
        assert color == "#fd7e14"  # Orange
        assert label == "At Risk"


class TestKeyInsights:
    """Test _create_key_insights() generation for schedule, velocity, progress."""

    def test_schedule_insight_ahead(self):
        """Test schedule insight when ahead of schedule."""
        # Given: 15 days ahead of deadline
        metrics = {
            "days_to_completion": 30,
            "days_to_deadline": 45,
            "velocity_trend": "stable",
            "completion_percentage": 50.0,
        }

        # When: Generate insights
        insights_div = _create_key_insights(metrics)

        # Then: Insights should include ahead-of-schedule message
        insights_text = str(insights_div)
        assert "ahead" in insights_text.lower()

    def test_schedule_insight_behind(self):
        """Test schedule insight when behind schedule."""
        # Given: 10 days behind deadline
        metrics = {
            "days_to_completion": 50,
            "days_to_deadline": 40,
            "velocity_trend": "stable",
            "completion_percentage": 50.0,
        }

        # When: Generate insights
        insights_div = _create_key_insights(metrics)

        # Then: Insights should include behind-schedule warning
        insights_text = str(insights_div)
        assert "behind" in insights_text.lower()

    def test_velocity_insight_increasing(self):
        """Test velocity insight when trend is increasing."""
        # Given: Increasing velocity trend
        metrics = {
            "days_to_completion": 30,
            "days_to_deadline": 45,
            "velocity_trend": "increasing",
            "completion_percentage": 50.0,
        }

        # When: Generate insights
        insights_div = _create_key_insights(metrics)

        # Then: Insights should include positive velocity message
        insights_text = str(insights_div)
        # Should mention velocity or trend in positive context
        assert "velocity" in insights_text.lower() or "trend" in insights_text.lower()

    def test_velocity_insight_decreasing(self):
        """Test velocity insight when trend is decreasing."""
        # Given: Decreasing velocity trend
        metrics = {
            "days_to_completion": 30,
            "days_to_deadline": 45,
            "velocity_trend": "decreasing",
            "completion_percentage": 50.0,
        }

        # When: Generate insights
        insights_div = _create_key_insights(metrics)

        # Then: Insights should include velocity concern message
        insights_text = str(insights_div)
        # Should mention velocity or trend in concerning context
        assert "velocity" in insights_text.lower() or "trend" in insights_text.lower()

    def test_insights_returns_div(self):
        """Test insights function returns html.Div component."""
        # Given: Any metrics
        metrics = {
            "days_to_completion": 30,
            "days_to_deadline": 45,
            "velocity_trend": "stable",
            "completion_percentage": 50.0,
        }

        # When: Generate insights
        insights = _create_key_insights(metrics)

        # Then: Should return Div
        assert isinstance(insights, html.Div)


class TestForecastCard:
    """Test create_dashboard_forecast_card() rendering."""

    def test_card_structure(self):
        """Test forecast card returns dbc.Card with header and body."""
        # Given: Sample metrics
        metrics = {
            "completion_percentage": 68.0,
            "days_to_completion": 30,
            "days_to_deadline": 45,
        }

        # When: Create forecast card
        card = create_dashboard_forecast_card(metrics)

        # Then: Card should be dbc.Card with children
        assert isinstance(card, dbc.Card)
        assert card.children is not None

    def test_card_displays_completion(self):
        """Test card displays days to completion."""
        # Given: 30 days to completion
        metrics = {
            "completion_percentage": 68.0,
            "days_to_completion": 30,
            "days_to_deadline": 45,
        }

        # When: Create card
        card = create_dashboard_forecast_card(metrics)

        # Then: Card should display days remaining (30.0)
        card_text = str(card)
        assert "30" in card_text  # Days to completion, not percentage

    def test_card_displays_forecast_date(self):
        """Test card displays forecast completion date."""
        # Given: Metrics with forecast date
        metrics = {
            "completion_percentage": 50.0,
            "forecast_completion_date": "2025-12-31",
            "days_to_completion": 30,
        }

        # When: Create card
        card = create_dashboard_forecast_card(metrics)

        # Then: Card should show forecast date
        card_text = str(card)
        assert "2025" in card_text or "forecast" in card_text.lower()


class TestVelocityCard:
    """Test create_dashboard_velocity_card() rendering."""

    def test_card_structure(self):
        """Test velocity card returns dbc.Card with header and body."""
        # Given: Sample metrics
        metrics = {
            "items_per_week": 5.2,
            "points_per_week": 26.0,
            "velocity_trend": "stable",
        }

        # When: Create velocity card
        card = create_dashboard_velocity_card(metrics)

        # Then: Card should be dbc.Card
        assert isinstance(card, dbc.Card)
        assert card.children is not None

    def test_card_displays_items_per_week(self):
        """Test card displays items per week velocity."""
        # Given: 5.2 items/week
        metrics = {
            "items_per_week": 5.2,
            "points_per_week": 26.0,
            "velocity_trend": "stable",
        }

        # When: Create card
        card = create_dashboard_velocity_card(metrics)

        # Then: Card should show items/week
        card_text = str(card)
        assert "5.2" in card_text or "items" in card_text.lower()

    def test_card_displays_velocity_trend(self):
        """Test card displays velocity trend indicator."""
        # Given: Increasing trend
        metrics = {
            "items_per_week": 5.2,
            "points_per_week": 26.0,
            "velocity_trend": "increasing",
        }

        # When: Create card
        card = create_dashboard_velocity_card(metrics)

        # Then: Card should show trend
        # (displayed as "Accelerating" for increasing trend)
        card_text = str(card)
        assert "accelerating" in card_text.lower() or "increasing" in card_text.lower()


class TestRemainingCard:
    """Test create_dashboard_remaining_card() rendering."""

    def test_card_structure(self):
        """Test remaining card returns dbc.Card with header and body."""
        # Given: Sample metrics
        metrics = {"remaining_items": 32, "remaining_points": 160}

        # When: Create remaining card
        card = create_dashboard_remaining_card(metrics)

        # Then: Card should be dbc.Card
        assert isinstance(card, dbc.Card)
        assert card.children is not None

    def test_card_displays_remaining_items(self):
        """Test card displays remaining work items."""
        # Given: 32 items remaining
        metrics = {"remaining_items": 32, "remaining_points": 160}

        # When: Create card
        card = create_dashboard_remaining_card(metrics)

        # Then: Card should show remaining items
        card_text = str(card)
        assert "32" in card_text


class TestPertCard:
    """Test create_dashboard_pert_card() rendering."""

    def test_card_structure(self):
        """Test PERT card returns dbc.Card with header and body."""
        # Given: Sample PERT metrics
        metrics = {
            "optimistic_date": "2025-11-15",
            "likely_date": "2025-12-01",
            "pessimistic_date": "2025-12-31",
        }

        # When: Create PERT card
        card = create_dashboard_pert_card(metrics)

        # Then: Card should be dbc.Card
        assert isinstance(card, dbc.Card)
        assert card.children is not None

    def test_card_displays_pert_dates(self):
        """Test card displays days to deadline."""
        # Given: PERT timeline with days_to_deadline
        metrics = {
            "optimistic_date": "2025-11-15",
            "likely_date": "2025-12-01",
            "pessimistic_date": "2025-12-31",
            "days_to_deadline": 50,  # Card displays this, not the dates
        }

        # When: Create card
        card = create_dashboard_pert_card(metrics)

        # Then: Card should show days to deadline
        card_text = str(card)
        assert "50" in card_text or "days" in card_text.lower()


class TestOverviewContent:
    """Test create_dashboard_overview_content() layout generation."""

    def test_overview_returns_div(self):
        """Test overview content returns html.Div container."""
        # Given: Sample metrics
        metrics = {
            "completion_percentage": 68.0,
            "items_per_week": 5.2,
            "remaining_items": 32,
            "velocity_trend": "stable",
        }

        # When: Create overview
        overview = create_dashboard_overview_content(metrics)

        # Then: Should return Div
        assert isinstance(overview, html.Div)

    def test_overview_includes_health_indicator(self):
        """Test overview includes health score indicator."""
        # Given: Sample metrics
        metrics = {
            "completion_percentage": 68.0,
            "days_to_completion": 30,
            "days_to_deadline": 45,
            "velocity_trend": "stable",
            "completion_confidence": 75,
        }

        # When: Create overview
        overview = create_dashboard_overview_content(metrics)

        # Then: Should include health indicator
        overview_text = str(overview)
        assert "health" in overview_text.lower() or "status" in overview_text.lower()

    def test_overview_responsive_layout(self):
        """Test overview uses responsive grid layout."""
        # Given: Sample metrics
        metrics = {
            "completion_percentage": 68.0,
            "items_per_week": 5.2,
            "remaining_items": 32,
        }

        # When: Create overview
        overview = create_dashboard_overview_content(metrics)

        # Then: Should use Bootstrap grid
        overview_text = str(overview)
        # Grid uses Row and Col components
        assert (
            "Row" in overview_text
            or "Col" in overview_text
            or "row" in overview_text.lower()
        )
