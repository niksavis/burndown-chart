import dash_bootstrap_components as dbc

from ui.budget_cards import create_cost_per_point_card


class TestCostPerPointCard:
    def test_points_tracking_disabled(self):
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

        text_content = self._extract_text(card)

        assert "Points Tracking Disabled" in text_content
        assert (
            "Enable Points Tracking" in text_content
            or "Points tracking is disabled" in text_content
        )

    def test_no_points_data(self):
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

        text_content = self._extract_text(card)

        assert (
            "no data" in text_content.lower() or "not available" in text_content.lower()
        )

    def test_with_valid_data(self):
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

        assert "metric-card-error" not in card.className  # type: ignore[attr-defined]

        text_content = self._extract_text(card)

        assert "85.50" in text_content
        assert "€" in text_content

    def test_with_baseline_comparison(self):
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

        text_content = self._extract_text(card)

        assert "80" in text_content or "80.00" in text_content
        assert "€" in text_content

    def _extract_text(self, component) -> str:
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
