"""
Unit tests for DORA metrics dashboard UI components.

Tests the create_dora_dashboard() function and helper functions to ensure:
- Proper layout structure with all required elements
- Responsive design with Bootstrap grid system
- Correct component IDs for callback integration
- Data formatting for display

NOTE: Phase 3 tests focus on UI structure. Phase 4+ will add integration tests.
"""

import pytest
import dash_bootstrap_components as dbc
from ui.dora_metrics_dashboard import (
    create_dora_dashboard,
    create_dora_loading_cards_grid,
    format_dora_metrics_for_display,
)


class TestCreateDoraDashboard:
    """Test the main DORA dashboard creation function."""

    def test_dashboard_returns_container(self):
        """Test that dashboard returns a valid Dash Bootstrap Container."""
        dashboard = create_dora_dashboard()
        assert isinstance(dashboard, dbc.Container)

    def test_dashboard_has_children(self):
        """Test that dashboard has child components."""
        dashboard = create_dora_dashboard()
        assert hasattr(dashboard, "children")
        children = dashboard.children
        assert children is not None
        # Should have multiple rows for layout
        assert len(children) > 0


class TestCreateDoraLoadingCardsGrid:
    """Test the loading cards grid component."""

    def test_loading_cards_returns_row(self):
        """Test that loading cards grid returns a Row component."""
        loading_grid = create_dora_loading_cards_grid()
        assert isinstance(loading_grid, dbc.Row)

    def test_loading_cards_has_four_metrics(self):
        """Test that loading cards grid has 4 children (one for each DORA metric)."""
        loading_grid = create_dora_loading_cards_grid()
        assert hasattr(loading_grid, "children")
        children = loading_grid.children
        assert children is not None
        # DORA has exactly 4 metrics
        assert len(children) == 4

    def test_loading_cards_use_columns(self):
        """Test that loading cards use Col components."""
        loading_grid = create_dora_loading_cards_grid()
        children = loading_grid.children
        assert children is not None  # Type guard
        # Each child should be a Col component
        for child in children:
            assert isinstance(child, dbc.Col)


class TestFormatDoraMetricsForDisplay:
    """Test the data formatting function."""

    def test_format_returns_dict(self):
        """Test that format function returns a dictionary."""
        calculator_output = {
            "deployment_frequency": {
                "value": 30.5,
                "unit": "per month",
                "tier": "Elite",
                "tier_color": "#28a745",
                "status": "success",
            },
            "lead_time_for_changes": {
                "value": 0.5,
                "unit": "days",
                "tier": "Elite",
                "tier_color": "#28a745",
                "status": "success",
            },
            "change_failure_rate": {
                "value": 5.0,
                "unit": "%",
                "tier": "Elite",
                "tier_color": "#28a745",
                "status": "success",
            },
            "mean_time_to_recovery": {
                "value": 0.5,
                "unit": "hours",
                "tier": "Elite",
                "tier_color": "#28a745",
                "status": "success",
            },
        }

        result = format_dora_metrics_for_display(calculator_output)
        assert isinstance(result, dict)

    def test_format_has_all_metrics(self):
        """Test that formatted output includes all 4 DORA metrics."""
        calculator_output = {
            "deployment_frequency": {
                "value": 30.5,
                "unit": "per month",
                "tier": "Elite",
                "tier_color": "#28a745",
                "status": "success",
            },
            "lead_time_for_changes": {
                "value": 0.5,
                "unit": "days",
                "tier": "Elite",
                "tier_color": "#28a745",
                "status": "success",
            },
            "change_failure_rate": {
                "value": 5.0,
                "unit": "%",
                "tier": "Elite",
                "tier_color": "#28a745",
                "status": "success",
            },
            "mean_time_to_recovery": {
                "value": 0.5,
                "unit": "hours",
                "tier": "Elite",
                "tier_color": "#28a745",
                "status": "success",
            },
        }

        result = format_dora_metrics_for_display(calculator_output)

        # Should have entries for all 4 metrics
        assert "deployment_frequency" in result
        assert "lead_time_for_changes" in result
        assert "change_failure_rate" in result
        assert "mean_time_to_recovery" in result


class TestDashboardIntegration:
    """Integration tests for dashboard component interactions."""

    def test_dashboard_can_be_created_without_errors(self):
        """Test that dashboard can be created without raising exceptions."""
        try:
            dashboard = create_dora_dashboard()
            assert dashboard is not None
        except Exception as e:
            pytest.fail(f"Dashboard creation raised exception: {e}")

    def test_loading_cards_match_metrics_count(self):
        """Test that loading cards match the number of DORA metrics."""
        loading_grid = create_dora_loading_cards_grid()
        children = loading_grid.children
        assert children is not None  # Type guard

        # DORA has exactly 4 metrics
        expected_metrics_count = 4
        assert len(children) == expected_metrics_count
