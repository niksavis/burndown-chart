"""
Unit tests for card components - specifically the create_info_card function.

Tests the contract-compliant card builder added in Phase 2.
"""

import pytest
from dash import html
import dash_bootstrap_components as dbc
from ui.cards import create_info_card


class TestCreateInfoCard:
    """Test create_info_card function following component contracts."""

    def test_create_card_basic(self):
        """Test card creation with minimal parameters."""
        card = create_info_card("Total Items", 42)

        assert isinstance(card, dbc.Card)
        assert card.id == "card-total-items"  # type: ignore[attr-defined]
        # Should have header and body
        assert len(card.children) >= 2  # type: ignore[attr-defined]

    def test_create_card_with_icon(self):
        """Test card with icon."""
        card = create_info_card("Remaining Items", 25, icon="tasks")

        assert card.id == "card-remaining-items"  # type: ignore[attr-defined]
        # Header should contain icon
        header = card.children[0]  # type: ignore[index]
        assert isinstance(header, dbc.CardHeader)

    def test_create_card_with_subtitle(self):
        """Test card with subtitle."""
        card = create_info_card(
            "Days to Completion", 53, subtitle="Based on current velocity"
        )

        body = card.children[1]  # type: ignore[index]
        assert isinstance(body, dbc.CardBody)
        # Body should have 2 children: value and subtitle
        assert len(body.children) == 2  # type: ignore[attr-defined]

    def test_create_card_variants(self):
        """Test all valid card variants."""
        variants = ["default", "primary", "success", "warning", "danger"]

        for variant in variants:
            card = create_info_card("Test", 100, variant=variant)
            # Card should be created successfully
            assert isinstance(card, dbc.Card)
            assert card.id == "card-test"  # type: ignore[attr-defined]

    def test_create_card_sizes(self):
        """Test card sizes."""
        sizes = ["sm", "md", "lg"]

        for size in sizes:
            card = create_info_card("Test", 100, size=size)
            # Card should be created successfully
            assert isinstance(card, dbc.Card)

    def test_create_card_clickable(self):
        """Test clickable card with footer."""
        card = create_info_card(
            "Remaining Items", 42, clickable=True, click_id="goto-burndown"
        )

        assert card.id == "card-remaining-items-goto-burndown"  # type: ignore[attr-defined]
        # Should have header, body, and footer
        assert len(card.children) == 3  # type: ignore[attr-defined]

        footer = card.children[2]  # type: ignore[index]
        assert isinstance(footer, dbc.CardFooter)

    def test_create_card_clickable_without_id_raises_error(self):
        """Test that clickable without click_id raises ValueError."""
        with pytest.raises(ValueError, match="click_id is required"):
            create_info_card("Test", 100, clickable=True)

        with pytest.raises(ValueError, match="click_id is required"):
            create_info_card("Test", 100, clickable=True, click_id="")

    def test_create_card_empty_title_raises_error(self):
        """Test that empty title raises ValueError."""
        with pytest.raises(ValueError, match="Title is required"):
            create_info_card("", 100)

        with pytest.raises(ValueError, match="Title is required"):
            create_info_card("   ", 100)

    def test_create_card_empty_value_raises_error(self):
        """Test that empty value raises ValueError."""
        with pytest.raises(ValueError, match="Value is required"):
            create_info_card("Test", "")

        with pytest.raises(ValueError, match="Value is required"):
            create_info_card("Test", "   ")

    def test_create_card_invalid_variant_raises_error(self):
        """Test that invalid variant raises ValueError."""
        with pytest.raises(ValueError, match="Invalid variant"):
            create_info_card("Test", 100, variant="invalid")

    def test_create_card_id_slugification(self):
        """Test that title is properly slugified for ID."""
        card = create_info_card("Days to Completion", 53)
        assert card.id == "card-days-to-completion"  # type: ignore[attr-defined]

        card = create_info_card("Total Work Items", 42)
        assert card.id == "card-total-work-items"  # type: ignore[attr-defined]

    def test_create_card_with_click_id(self):
        """Test card ID generation with click_id."""
        card = create_info_card("Items", 42, clickable=True, click_id="burndown-chart")
        assert card.id == "card-items-burndown-chart"  # type: ignore[attr-defined]

    def test_create_card_with_kwargs(self):
        """Test card with additional kwargs."""
        custom_class = "my-custom-card"
        card = create_info_card("Test", 100, className=custom_class)

        assert custom_class in card.className  # type: ignore[attr-defined,operator]

    def test_create_card_with_custom_style(self):
        """Test card with custom style override."""
        custom_style = {"backgroundColor": "red", "border": "2px solid black"}
        card = create_info_card("Test", 100, style=custom_style)

        # Custom styles should be merged with design token styles
        assert "backgroundColor" in card.style  # type: ignore[attr-defined,operator]
        assert card.style["backgroundColor"] == "red"  # type: ignore[attr-defined,index]

    def test_create_card_with_icon_prefix(self):
        """Test card with icon that already has fa- prefix."""
        card = create_info_card("Test", 100, icon="fas fa-check")

        # Should create successfully without error
        assert isinstance(card, dbc.Card)

    def test_create_card_numeric_value(self):
        """Test card with numeric values."""
        card = create_info_card("Count", 42)
        body = card.children[1]  # type: ignore[index]
        # Value should be converted to string
        assert "42" in str(body)

    def test_create_card_float_value(self):
        """Test card with float value."""
        card = create_info_card("PERT Factor", 1.5)
        body = card.children[1]  # type: ignore[index]
        assert "1.5" in str(body)

    def test_create_card_clickable_has_hover_class(self):
        """Test that clickable cards get the clickable class."""
        card = create_info_card("Test", 100, clickable=True, click_id="test-click")

        # Should have card-clickable class for CSS hover effects
        assert "card-clickable" in card.className  # type: ignore[attr-defined,operator]


class TestInfoCardIntegration:
    """Integration tests for info cards."""

    def test_card_in_grid(self):
        """Test cards work in grid layout."""
        card1 = create_info_card("Metric 1", 100, variant="primary")
        card2 = create_info_card("Metric 2", 200, variant="success")
        card3 = create_info_card("Metric 3", 300, variant="warning")

        grid = html.Div([card1, card2, card3], className="row")

        assert len(grid.children) == 3  # type: ignore[attr-defined]

    def test_card_consistency_across_variants(self):
        """Test that cards maintain consistent structure across variants."""
        variants = ["default", "primary", "success", "warning", "danger"]
        cards = [create_info_card("Test", 100, variant=v) for v in variants]

        # All cards should have same number of children (header + body)
        for card in cards:
            assert len(card.children) == 2  # type: ignore[attr-defined]

    def test_card_with_all_features(self):
        """Test card with all features enabled."""
        card = create_info_card(
            title="Completion Forecast",
            value="2025-12-31",
            icon="calendar-check",
            subtitle="Based on current velocity",
            variant="primary",
            clickable=True,
            click_id="goto-forecast",
            size="lg",
            className="featured-card",
        )

        # Should have header, body, and footer
        assert len(card.children) == 3  # type: ignore[attr-defined]
        # Should have correct ID
        assert card.id == "card-completion-forecast-goto-forecast"  # type: ignore[attr-defined]
        # Should have custom class
        assert "featured-card" in card.className  # type: ignore[attr-defined,operator]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
