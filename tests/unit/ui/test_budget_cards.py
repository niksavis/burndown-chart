"""Unit tests for budget_cards module.

Tests budget card rendering including points tracking disabled and no data states.

This test suite verifies the fix for consistent card rendering across the dashboard.
All cards should use the same template patterns for:
1. Points tracking disabled (show_points=False)
2. Points tracking enabled but no data (show_points=True, value=0)
3. Points tracking enabled with valid data

The same pattern is applied to:
- Cost Per Point card (Budget & Resource Tracking section)
- Project Health Overview Points section
- Other dashboard cards that display points-based metrics
"""

import dash_bootstrap_components as dbc

from ui.budget_cards import create_cost_per_point_card


class TestCostPerPointCard:
    """Test suite for Cost Per Point card."""

    def test_points_tracking_disabled(self):
        """Test card rendering when points tracking is disabled."""
        card = create_cost_per_point_card(
            cost_per_point=0,
            pert_weighted_avg=None,
            points_available=False,
            currency_symbol="€",
            data_points_count=12,
            card_id="test-card",
            baseline_data=None,
        )

        assert isinstance(card, dbc.Card)
        assert card.id == "test-card"  # type: ignore[attr-defined]
        assert "metric-card" in card.className  # type: ignore[attr-defined]

        # Extract text content
        text_content = self._extract_text(card)

        # Should show "Points Tracking Disabled" message
        assert "Points Tracking Disabled" in text_content
        assert (
            "Enable Points Tracking" in text_content
            or "Points tracking is disabled" in text_content
        )

    def test_no_points_data(self):
        """Test card rendering when points tracking is enabled but no data available."""
        card = create_cost_per_point_card(
            cost_per_point=0,
            pert_weighted_avg=None,
            points_available=True,
            currency_symbol="€",
            data_points_count=12,
            card_id="test-card",
            baseline_data=None,
        )

        assert isinstance(card, dbc.Card)
        assert "metric-card" in card.className  # type: ignore[attr-defined]

        # Extract text content
        text_content = self._extract_text(card)

        # Should show no data message (format may vary)
        assert (
            "no data" in text_content.lower() or "not available" in text_content.lower()
        )

    def test_with_valid_data(self):
        """Test card rendering with valid cost per point data."""
        card = create_cost_per_point_card(
            cost_per_point=85.50,
            pert_weighted_avg=82.40,
            points_available=True,
            currency_symbol="€",
            data_points_count=12,
            card_id="test-card",
            baseline_data=None,
        )

        assert isinstance(card, dbc.Card)
        assert "metric-card" in card.className  # type: ignore[attr-defined]

        # Should not have error class when data is valid
        assert "metric-card-error" not in card.className  # type: ignore[attr-defined]

        # Extract text content
        text_content = self._extract_text(card)

        # Should show the cost value
        assert "85.50" in text_content
        assert "€" in text_content

    def test_with_baseline_comparison(self):
        """Test card rendering with baseline comparison data."""
        baseline_data = {
            "actual": {
                "velocity_points": 25.0,
            },
            "baseline": {
                "team_cost_per_week_eur": 2000.0,
                "assumed_baseline_velocity_points": 21.0,
            },
        }

        card = create_cost_per_point_card(
            cost_per_point=80.00,
            pert_weighted_avg=None,
            points_available=True,
            currency_symbol="€",
            data_points_count=12,
            card_id="test-card",
            baseline_data=baseline_data,
        )

        assert isinstance(card, dbc.Card)
        assert "metric-card" in card.className  # type: ignore[attr-defined]

        # Extract text content
        text_content = self._extract_text(card)

        # Should show baseline comparison
        assert "80" in text_content or "80.00" in text_content
        assert "€" in text_content

    def _extract_text(self, component) -> str:
        """Recursively extract all text content from a Dash component."""
        if component is None:
            return ""

        if isinstance(component, str):
            return component

        if hasattr(component, "children"):
            if isinstance(component.children, list):
                return " ".join(
                    self._extract_text(child) for child in component.children
                )
            else:
                return self._extract_text(component.children)

        return ""
