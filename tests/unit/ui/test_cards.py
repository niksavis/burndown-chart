import dash_bootstrap_components as dbc
import pytest
from dash import html

from ui.cards import create_info_card


class TestCreateInfoCard:
    def test_create_card_basic(self):
        card = create_info_card("Total Items", 42)

        assert isinstance(card, dbc.Card)
        assert card.id == "card-total-items"  # type: ignore[attr-defined]
        assert len(card.children) >= 2  # type: ignore[attr-defined]

    def test_create_card_with_icon(self):
        card = create_info_card("Remaining Items", 25, icon="tasks")

        assert card.id == "card-remaining-items"  # type: ignore[attr-defined]
        header = card.children[0]  # type: ignore[index]
        assert isinstance(header, dbc.CardHeader)

    def test_create_card_with_subtitle(self):
        card = create_info_card(
            "Days to Completion", 53, subtitle="Based on current velocity"
        )

        body = card.children[1]  # type: ignore[index]
        assert isinstance(body, dbc.CardBody)
        assert len(body.children) == 2  # type: ignore[attr-defined]

    def test_create_card_variants(self):
        variants = ["default", "primary", "success", "warning", "danger"]

        for variant in variants:
            card = create_info_card("Test", 100, variant=variant)
            assert isinstance(card, dbc.Card)
            assert card.id == "card-test"  # type: ignore[attr-defined]

    def test_create_card_sizes(self):
        sizes = ["sm", "md", "lg"]

        for size in sizes:
            card = create_info_card("Test", 100, size=size)
            assert isinstance(card, dbc.Card)

    def test_create_card_clickable(self):
        card = create_info_card(
            "Remaining Items", 42, clickable=True, click_id="goto-burndown"
        )

        assert card.id == "card-remaining-items-goto-burndown"  # type: ignore[attr-defined]
        assert len(card.children) == 3  # type: ignore[attr-defined]

        footer = card.children[2]  # type: ignore[index]
        assert isinstance(footer, dbc.CardFooter)

    def test_create_card_clickable_without_id_raises_error(self):
        with pytest.raises(ValueError, match="click_id is required"):
            create_info_card("Test", 100, clickable=True)

        with pytest.raises(ValueError, match="click_id is required"):
            create_info_card("Test", 100, clickable=True, click_id="")

    def test_create_card_empty_title_raises_error(self):
        with pytest.raises(ValueError, match="Title is required"):
            create_info_card("", 100)

        with pytest.raises(ValueError, match="Title is required"):
            create_info_card("   ", 100)

    def test_create_card_empty_value_raises_error(self):
        with pytest.raises(ValueError, match="Value is required"):
            create_info_card("Test", "")

        with pytest.raises(ValueError, match="Value is required"):
            create_info_card("Test", "   ")

    def test_create_card_invalid_variant_raises_error(self):
        with pytest.raises(ValueError, match="Invalid variant"):
            create_info_card("Test", 100, variant="invalid")

    def test_create_card_id_slugification(self):
        card = create_info_card("Days to Completion", 53)
        assert card.id == "card-days-to-completion"  # type: ignore[attr-defined]

        card = create_info_card("Total Work Items", 42)
        assert card.id == "card-total-work-items"  # type: ignore[attr-defined]

    def test_create_card_with_click_id(self):
        card = create_info_card("Items", 42, clickable=True, click_id="burndown-chart")
        assert card.id == "card-items-burndown-chart"  # type: ignore[attr-defined]

    def test_create_card_with_kwargs(self):
        custom_class = "my-custom-card"
        card = create_info_card("Test", 100, className=custom_class)

        assert custom_class in card.className  # type: ignore[attr-defined,operator]

    def test_create_card_with_custom_style(self):
        custom_style = {"backgroundColor": "red", "border": "2px solid black"}
        card = create_info_card("Test", 100, style=custom_style)

        assert "backgroundColor" in card.style  # type: ignore[attr-defined,operator]
        assert card.style["backgroundColor"] == "red"  # type: ignore[attr-defined,index]

    def test_create_card_with_icon_prefix(self):
        card = create_info_card("Test", 100, icon="fas fa-check")

        assert isinstance(card, dbc.Card)

    def test_create_card_numeric_value(self):
        card = create_info_card("Count", 42)
        body = card.children[1]  # type: ignore[index]
        assert "42" in str(body)

    def test_create_card_float_value(self):
        card = create_info_card("PERT Factor", 1.5)
        body = card.children[1]  # type: ignore[index]
        assert "1.5" in str(body)

    def test_create_card_clickable_has_hover_class(self):
        card = create_info_card("Test", 100, clickable=True, click_id="test-click")

        assert "card-clickable" in card.className  # type: ignore[attr-defined,operator]


class TestInfoCardIntegration:
    def test_card_in_grid(self):
        card1 = create_info_card("Metric 1", 100, variant="primary")
        card2 = create_info_card("Metric 2", 200, variant="success")
        card3 = create_info_card("Metric 3", 300, variant="warning")

        grid = html.Div([card1, card2, card3], className="row")

        assert len(grid.children) == 3  # type: ignore[attr-defined]

    def test_card_consistency_across_variants(self):
        variants = ["default", "primary", "success", "warning", "danger"]
        cards = [create_info_card("Test", 100, variant=v) for v in variants]

        for card in cards:
            assert len(card.children) == 2  # type: ignore[attr-defined]

    def test_card_with_all_features(self):
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

        assert len(card.children) == 3  # type: ignore[attr-defined]
        assert card.id == "card-completion-forecast-goto-forecast"  # type: ignore[attr-defined]
        assert "featured-card" in card.className  # type: ignore[attr-defined,operator]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
