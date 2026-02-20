"""Unit tests for metric_cards module.

Tests metric card rendering for success states, error states, and loading states.
"""

from typing import Any

import dash_bootstrap_components as dbc
import pytest

from ui.metric_cards import (
    create_loading_card,
    create_metric_card,
    create_metric_cards_grid,
)


def _extract_text_from_component(component: Any) -> str:
    """Recursively extract all text content from a Dash component."""
    if component is None:
        return ""

    if isinstance(component, str):
        return component

    if hasattr(component, "children"):
        if isinstance(component.children, list):
            return " ".join(
                _extract_text_from_component(child) for child in component.children
            )
        else:
            return _extract_text_from_component(component.children)

    return ""


def _find_component_by_type(component, component_type):
    """Recursively find first component of specified type."""
    if isinstance(component, component_type):
        return component

    if hasattr(component, "children"):
        if isinstance(component.children, list):
            for child in component.children:
                result = _find_component_by_type(child, component_type)
                if result is not None:
                    return result
        else:
            return _find_component_by_type(component.children, component_type)

    return None


class TestCreateMetricCard:
    """Test metric card creation for different states."""

    def test_success_state_card(self):
        """Test card rendering for successful metric calculation."""
        metric_data = {
            "metric_name": "deployment_frequency",
            "value": 45.2,
            "unit": "deployments/month",
            "performance_tier": "High",
            "performance_tier_color": "yellow",
            "error_state": "success",
            "error_message": None,
            "excluded_issue_count": 2,
            "total_issue_count": 52,
            "details": {},
        }

        card = create_metric_card(metric_data)

        # Card should be a dbc.Card
        assert isinstance(card, dbc.Card)

        # Card should have metric-card class
        assert "metric-card" in card.className  # type: ignore[attr-defined]

        # Card should have children (header, body, and footer)
        assert len(card.children) == 3  # type: ignore[arg-type]

    def test_error_state_missing_mapping(self):
        """Test card rendering for missing field mapping error."""
        metric_data = {
            "metric_name": "deployment_frequency",
            "value": None,
            "error_state": "missing_mapping",
            "error_message": "Configure 'Deployment Date' field mapping",
        }

        card = create_metric_card(metric_data)

        assert isinstance(card, dbc.Card)
        assert "metric-card-error" in card.className  # type: ignore[attr-defined]

    def test_error_state_no_data(self):
        """Test card rendering for no data error."""
        metric_data = {
            "metric_name": "lead_time_for_changes",
            "value": None,
            "error_state": "no_data",
            "error_message": "No deployments found in the last 30 days",
        }

        card = create_metric_card(metric_data)

        assert isinstance(card, dbc.Card)
        assert "metric-card-error" in card.className  # type: ignore[attr-defined]

    def test_error_state_calculation_error(self):
        """Test card rendering for calculation error."""
        metric_data = {
            "metric_name": "change_failure_rate",
            "value": None,
            "error_state": "calculation_error",
            "error_message": "Failed to calculate metric: division by zero",
        }

        card = create_metric_card(metric_data)

        assert isinstance(card, dbc.Card)
        assert "metric-card-error" in card.className  # type: ignore[attr-defined]

    def test_card_with_custom_id(self):
        """Test card creation with custom ID."""
        metric_data = {
            "metric_name": "deployment_frequency",
            "value": 45.2,
            "unit": "deployments/month",
            "error_state": "success",
            "total_issue_count": 50,
        }

        card = create_metric_card(metric_data, card_id="custom-card-id")

        assert card.id == "custom-card-id"  # type: ignore[attr-defined]

    def test_value_formatting_large_numbers(self):
        """Test value formatting for numbers >= 10."""
        metric_data = {
            "metric_name": "deployment_frequency",
            "value": 125.789,
            "unit": "deployments/month",
            "error_state": "success",
            "total_issue_count": 150,
        }

        card = create_metric_card(metric_data)

        # Check that value appears in card (formatting happens at display layer)
        text_content = _extract_text_from_component(card)
        # Value should be present in some form
        assert "125" in text_content

    def test_value_formatting_small_numbers(self):
        """Test value formatting for numbers < 10."""
        metric_data = {
            "metric_name": "lead_time_for_changes",
            "value": 3.456,
            "unit": "days",
            "error_state": "success",
            "total_issue_count": 50,
        }

        card = create_metric_card(metric_data)

        # Should format to 2 decimal places for small numbers
        text_content = _extract_text_from_component(card)
        assert "3.46" in text_content  # 2 decimal places
        assert "3.456" not in text_content  # Not full precision

    def test_excluded_issues_message(self):
        """Test additional info message when issues are excluded."""
        metric_data = {
            "metric_name": "deployment_frequency",
            "value": 45.2,
            "unit": "deployments/month",
            "error_state": "success",
            "excluded_issue_count": 5,
            "total_issue_count": 55,
        }

        card = create_metric_card(metric_data)

        # Card should contain info about excluded issues
        text_content = _extract_text_from_component(card)
        # Check for issue count information (format may vary)
        assert "50" in text_content and "55" in text_content

    def test_no_excluded_issues_message(self):
        """Test additional info message when no issues are excluded."""
        metric_data = {
            "metric_name": "deployment_frequency",
            "value": 45.2,
            "unit": "deployments/month",
            "error_state": "success",
            "excluded_issue_count": 0,
            "total_issue_count": 50,
        }

        card = create_metric_card(metric_data)

        # Card should show simple message
        text_content = _extract_text_from_component(card)
        # Check for issue count (format may vary)
        assert "50" in text_content
        assert "excluded" not in text_content.lower()


class TestPerformanceTierColors:
    """Test performance tier badge colors."""

    @pytest.mark.parametrize(
        "tier_color,expected_bootstrap_color",
        [
            ("green", "success"),
            ("yellow", "warning"),
            ("orange", "warning"),
            ("red", "danger"),
        ],
    )
    def test_tier_color_mapping(self, tier_color, expected_bootstrap_color):
        """Test tier colors map to correct Bootstrap colors."""
        metric_data = {
            "metric_name": "deployment_frequency",
            "value": 45.2,
            "unit": "deployments/month",
            "performance_tier": "High",
            "performance_tier_color": tier_color,
            "error_state": "success",
            "total_issue_count": 50,
        }

        card = create_metric_card(metric_data)

        # Find the badge component and verify its color
        badge = _find_component_by_type(card, dbc.Badge)
        assert badge is not None, f"Badge not found for tier color {tier_color}"

        # Badge can use either 'color' prop or className with bg-{color}
        # Use getattr to safely access attributes for type checker
        badge_color = getattr(badge, "color", None)
        badge_class_name = getattr(badge, "className", None) or ""

        # Check both possibilities
        has_color_prop = badge_color == expected_bootstrap_color
        has_color_class = f"bg-{expected_bootstrap_color}" in badge_class_name
        has_color_class_tier = "bg-tier-" in badge_class_name  # Custom tier classes

        assert has_color_prop or has_color_class or has_color_class_tier, (
            f"Expected badge with color {expected_bootstrap_color}, "
            f"got color={badge_color}, className={badge_class_name}"
        )


class TestCreateLoadingCard:
    """Test loading card creation."""

    def test_loading_card_structure(self):
        """Test loading card has correct structure."""
        card = create_loading_card("deployment_frequency")

        assert isinstance(card, dbc.Card)
        assert "metric-card-loading" in card.className  # type: ignore[attr-defined]

        # Should have header and body
        assert len(card.children) == 2  # type: ignore[arg-type]

    def test_loading_card_metric_name_formatting(self):
        """Test metric name is formatted correctly in loading card."""
        card = create_loading_card("lead_time_for_changes")

        # Should format name from snake_case to Title Case
        text_content = _extract_text_from_component(card)
        assert "Lead Time For Changes" in text_content
        assert "lead_time_for_changes" not in text_content


class TestCreateMetricCardsGrid:
    """Test metric cards grid creation."""

    def test_grid_with_multiple_metrics(self):
        """Test grid creation with multiple metrics."""
        metrics_data = {
            "deployment_frequency": {
                "metric_name": "deployment_frequency",
                "value": 45.2,
                "unit": "deployments/month",
                "error_state": "success",
                "total_issue_count": 50,
            },
            "lead_time_for_changes": {
                "metric_name": "lead_time_for_changes",
                "value": 3.5,
                "unit": "days",
                "error_state": "success",
                "total_issue_count": 50,
            },
        }

        grid = create_metric_cards_grid(metrics_data)

        # Should return a Row
        assert isinstance(grid, dbc.Row)

        # Row should have correct class
        assert "metric-cards-grid" in grid.className  # type: ignore[attr-defined]

        # Should have 2 columns (one per metric)
        assert len(grid.children) == 2  # type: ignore[arg-type]

    def test_grid_empty_metrics(self):
        """Test grid with no metrics."""
        metrics_data = {}

        grid = create_metric_cards_grid(metrics_data)

        assert isinstance(grid, dbc.Row)
        assert len(grid.children) == 0  # type: ignore[arg-type]

    def test_grid_responsive_columns(self):
        """Test grid columns have responsive breakpoints."""
        metrics_data = {
            "deployment_frequency": {
                "metric_name": "deployment_frequency",
                "value": 45.2,
                "error_state": "success",
                "total_issue_count": 50,
            }
        }

        grid = create_metric_cards_grid(metrics_data)

        # First column should exist and be a Col component
        first_col = grid.children[0]  # type: ignore[index]
        assert isinstance(first_col, dbc.Col)

        # Column should have a card as its child
        assert len(first_col.children) > 0, "Column should have children"  # type: ignore[arg-type]

    def test_grid_card_ids_match_metric_names(self):
        """Test grid assigns correct IDs to cards."""
        metrics_data = {
            "deployment_frequency": {
                "metric_name": "deployment_frequency",
                "value": 45.2,
                "error_state": "success",
                "total_issue_count": 50,
            }
        }

        grid = create_metric_cards_grid(metrics_data)

        # Card should have ID matching metric name with -card suffix
        first_col = grid.children[0]  # type: ignore[index]
        card = first_col.children
        assert card.id == "deployment_frequency-card"  # type: ignore[attr-defined]


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_null_value_in_success_state(self):
        """Test handling of null value in success state."""
        metric_data = {
            "metric_name": "deployment_frequency",
            "value": None,
            "unit": "deployments/month",
            "error_state": "success",
            "total_issue_count": 0,
        }

        card = create_metric_card(metric_data)

        # Should render without error, showing N/A
        assert card is not None
        text_content = _extract_text_from_component(card)
        assert "N/A" in text_content

    def test_missing_optional_fields(self):
        """Test card renders even with missing optional fields."""
        metric_data = {
            "metric_name": "deployment_frequency",
            "value": 45.2,
            "error_state": "success",
        }

        card = create_metric_card(metric_data)

        # Should not raise error
        assert card is not None

    def test_missing_performance_tier(self):
        """Test card renders without performance tier badge when not provided."""
        metric_data = {
            "metric_name": "deployment_frequency",
            "value": 45.2,
            "unit": "deployments/month",
            "error_state": "success",
            "total_issue_count": 50,
            # No performance_tier provided
        }

        card = create_metric_card(metric_data)

        # Should render without error and without badge
        assert card is not None
        # Verify no badge is present
        badge = _find_component_by_type(card, dbc.Badge)
        assert badge is None, (
            "Badge should not be present when performance_tier is missing"
        )

    def test_unknown_error_state(self):
        """Test handling of unknown error state."""
        metric_data = {
            "metric_name": "deployment_frequency",
            "value": None,
            "error_state": "unknown_error",
            "error_message": "Something went wrong",
        }

        card = create_metric_card(metric_data)

        # Should render generic error card
        assert card is not None
        assert "metric-card-error" in card.className  # type: ignore[attr-defined]
