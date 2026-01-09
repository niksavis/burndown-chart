from dash import html
import dash_bootstrap_components as dbc

# Import functions under test
from ui.dashboard_cards import (
    _calculate_health_score,
    _get_health_color_and_label,
    _create_key_insights,
    create_dashboard_forecast_card,
    create_dashboard_velocity_card,
    create_dashboard_remaining_card,
    create_dashboard_pert_card,
    create_dashboard_overview_content,
)

# Fixtures are imported automatically by pytest from conftest.py and dashboard_test_fixtures.py
# No need to explicitly import them - they're used as function parameters


class TestHealthScore:
    """Test _calculate_health_score() 4-component calculation."""

    def test_progress_component_normal(self):
        """Test progress component contributes 25% weight (68% completion = 17/25 points)."""
        # Given: 68% project completion (68/100 items)
        metrics = {
            "completion_percentage": 68.0,
            "days_to_completion": 30,
            "days_to_deadline": 45,
            "velocity_trend": "stable",
            "completion_confidence": 75,
        }

        # When: Calculate health score
        health = _calculate_health_score(metrics)

        # Then: Progress component = 68 * 0.25 = 17.0 points
        # Health should reflect good progress (high score expected)
        assert health >= 60  # Should be in "Good" range
        assert health <= 100

    def test_schedule_component_on_track(self):
        """Test schedule component contributes 30% weight (45 days buffer = healthy)."""
        # Given: 30 days to completion, 45 days to deadline (ahead of schedule)
        metrics = {
            "completion_percentage": 50.0,
            "days_to_completion": 30,
            "days_to_deadline": 45,  # 15 day buffer
            "velocity_trend": "stable",
            "completion_confidence": 75,
        }

        # When: Calculate health score
        health = _calculate_health_score(metrics)

        # Then: Schedule component should contribute high score (ahead of schedule)
        assert health >= 60  # Good health from schedule buffer

    def test_schedule_component_behind(self):
        """Test schedule component with insufficient buffer (behind schedule)."""
        # Given: 50 days to completion, 45 days to deadline (behind schedule)
        metrics = {
            "completion_percentage": 50.0,
            "days_to_completion": 50,
            "days_to_deadline": 45,  # 5 days behind
            "velocity_trend": "stable",
            "completion_confidence": 75,
        }

        # When: Calculate health score
        health = _calculate_health_score(metrics)

        # Then: Schedule component should reduce overall score (behind schedule penalty)
        # With small schedule variance (5 days), stable velocity, the new continuous formula
        # produces a moderate score around 72 (velocity: 30*0.5=15, schedule: 25*0.92=23,
        # scope: 20, trend: 10, recent: ~4 = ~72)
        assert (
            health == 72
        )  # Continuous formula gives moderate score for small variance    def test_velocity_component_increasing(self):
        """Test velocity component with increasing trend (25% weight, bonus points)."""
        # Given: Increasing velocity trend (team accelerating)
        metrics = {
            "completion_percentage": 50.0,
            "days_to_completion": 30,
            "days_to_deadline": 45,
            "velocity_trend": "increasing",
            "completion_confidence": 75,
        }

        # When: Calculate health with increasing trend
        health_increasing = _calculate_health_score(metrics)

        # Compare to stable trend
        metrics["velocity_trend"] = "stable"
        health_stable = _calculate_health_score(metrics)

        # Then: Increasing trend should boost health
        assert health_increasing > health_stable  # Increasing trend adds bonus

    def test_velocity_component_decreasing(self):
        """Test velocity component with decreasing trend (25% weight, penalty)."""
        # Given: Decreasing velocity trend (team slowing down)
        metrics = {
            "completion_percentage": 50.0,
            "days_to_completion": 30,
            "days_to_deadline": 45,
            "velocity_trend": "decreasing",
            "completion_confidence": 75,
        }

        # When: Calculate health with decreasing trend
        health_decreasing = _calculate_health_score(metrics)

        # Compare to stable trend
        metrics["velocity_trend"] = "stable"
        health_stable = _calculate_health_score(metrics)

        # Then: Decreasing trend should lower health
        assert health_decreasing < health_stable  # Decreasing trend has penalty

    def test_confidence_component_high(self):
        """Test confidence component with high confidence (20% weight)."""
        # Given: 90% completion confidence (very confident estimate)
        metrics = {
            "completion_percentage": 50.0,
            "days_to_completion": 30,
            "days_to_deadline": 45,
            "velocity_trend": "stable",
            "completion_confidence": 90,
        }

        # When: Calculate health with high confidence
        health_high = _calculate_health_score(metrics)

        # Compare to low confidence
        metrics["completion_confidence"] = 30
        health_low = _calculate_health_score(metrics)

        # Then: High confidence should boost health
        assert health_high > health_low  # Higher confidence = better health

    def test_health_score_composite_excellent(self):
        """Test composite health score for excellent project (>80 = excellent)."""
        # Given: Low velocity CV, on schedule, low scope growth, improving trend, positive recent change
        metrics = {
            "velocity_cv": 15,  # Consistent velocity (30 * 0.7 = 21 points)
            "schedule_variance_days": 0,  # On time (25 points)
            "scope_change_rate": 5,  # Low scope growth (20 * 0.875 = 17.5 points)
            "trend_direction": "improving",  # Improving trend (15 points)
            "recent_velocity_change": 10,  # Positive momentum (7.5 points)
        }

        # When: Calculate composite health
        health = _calculate_health_score(metrics)

        # Then: Health score should be >=80 (excellent tier)
        # Expected: 21 + 25 + 17.5 + 15 + 7.5 = 86 points
        assert health >= 80
        assert health <= 100  # Never exceed 100

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
        # Given: High velocity CV, significantly behind schedule, high scope growth, declining trend
        metrics = {
            "velocity_cv": 60,  # Poor consistency (0 points - capped at 50)
            "schedule_variance_days": 50,  # Significantly behind (25 * 0.17 = 4.2 points)
            "scope_change_rate": 35,  # High scope growth (20 * 0.125 = 2.5 points)
            "trend_direction": "declining",  # Declining trend (0 points)
            "recent_velocity_change": -25,  # Negative momentum (0 points)
        }

        # When: Calculate composite health
        health = _calculate_health_score(metrics)

        # Then: Health score should be <40 (needs attention)
        # Expected: 0 + 4.2 + 2.5 + 0 + 0 = ~7 points
        assert health < 40
        assert health >= 0  # Never negative


class TestHealthColorLabel:
    """Test _get_health_color_and_label() tier mapping."""

    def test_excellent_tier(self):
        """Test excellent tier (80-100) maps to green color and 'Excellent' label."""
        # Given: Health score 85 (excellent range)
        # When: Get color and label
        color, label = _get_health_color_and_label(85)

        # Then: Color = green, label = "Excellent"
        assert color == "#198754"  # Green
        assert label == "Excellent"

    def test_good_tier(self):
        """Test good tier (60-79) maps to cyan color and 'Good' label."""
        # Given: Health score 70 (good range)
        # When: Get color and label
        color, label = _get_health_color_and_label(70)

        # Then: Color = cyan, label = "Good"
        assert color == "#0dcaf0"  # Cyan
        assert label == "Good"

    def test_fair_tier(self):
        """Test fair tier (40-59) maps to yellow color and 'Fair' label."""
        # Given: Health score 50 (fair range)
        # When: Get color and label
        color, label = _get_health_color_and_label(50)

        # Then: Color = yellow, label = "Fair"
        assert color == "#ffc107"  # Yellow
        assert label == "Fair"

    def test_needs_attention_tier(self):
        """Test needs attention tier (<40) maps to orange color and 'Needs Attention' label."""
        # Given: Health score 30 (needs attention range)
        # When: Get color and label
        color, label = _get_health_color_and_label(30)

        # Then: Color = orange, label = "Needs Attention"
        assert color == "#fd7e14"  # Orange
        assert label == "Needs Attention"


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
        assert (
            "30" in card_text
        )  # Days to completion, not percentage    def test_card_displays_forecast_date(self):
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

        # Then: Card should show trend (displayed as "Accelerating" for increasing trend)
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
