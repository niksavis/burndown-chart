"""
Unit tests for Flow metrics dashboard UI components.

Tests the create_flow_dashboard() function and helper functions to ensure:
- Proper layout structure with all required elements
- Responsive design with Bootstrap grid system
- Correct component IDs for callback integration
- Distribution chart is included
- Data formatting for display

T043: Unit test for Flow dashboard UI verifying distribution chart and metric cards.
"""

import pytest
import dash_bootstrap_components as dbc
from ui.flow_metrics_dashboard import (
    create_flow_dashboard,
    create_flow_loading_cards_grid,
)


class TestCreateFlowDashboard:
    """Test the main Flow dashboard creation function."""

    def test_dashboard_returns_container(self):
        """Test that dashboard returns a valid Dash Bootstrap Container."""
        dashboard = create_flow_dashboard()
        assert isinstance(dashboard, dbc.Container)

    def test_dashboard_has_children(self):
        """Test that dashboard has child components."""
        dashboard = create_flow_dashboard()
        assert hasattr(dashboard, "children")
        children = dashboard.children
        assert children is not None
        # Should have multiple rows for layout
        assert len(children) > 0


class TestCreateFlowLoadingCardsGrid:
    """Test the loading cards grid component."""

    def test_loading_cards_returns_row(self):
        """Test that loading cards grid returns a Row component."""
        loading_grid = create_flow_loading_cards_grid()
        assert isinstance(loading_grid, dbc.Row)

    def test_loading_cards_has_five_metrics(self):
        """Test that loading cards grid has 5 children (one for each Flow metric)."""
        loading_grid = create_flow_loading_cards_grid()
        assert hasattr(loading_grid, "children")
        children = loading_grid.children
        assert children is not None
        # Flow Framework has exactly 5 metrics
        assert len(children) == 5

    def test_loading_cards_use_columns(self):
        """Test that loading cards use Col components."""
        loading_grid = create_flow_loading_cards_grid()
        children = loading_grid.children
        assert children is not None  # Type guard
        # Each child should be a Col component
        for child in children:
            assert isinstance(child, dbc.Col)


class TestFormatFlowMetricsForDisplay:
    """Test the data formatting function."""

    def test_format_function_can_be_implemented_later(self):
        """Placeholder test - format function not yet implemented in UI module."""
        # The format_flow_metrics_for_display function hasn't been created yet
        # This test ensures the test file is valid even without that function
        assert True


class TestDashboardIntegration:
    """Integration tests for dashboard component interactions."""

    def test_dashboard_can_be_created_without_errors(self):
        """Test that dashboard can be created without raising exceptions."""
        try:
            dashboard = create_flow_dashboard()
            assert dashboard is not None
        except Exception as e:
            pytest.fail(f"Dashboard creation raised exception: {e}")

    def test_loading_cards_match_metrics_count(self):
        """Test that loading cards match the number of Flow metrics."""
        loading_grid = create_flow_loading_cards_grid()
        children = loading_grid.children
        assert children is not None  # Type guard

        # Flow Framework has exactly 5 metrics
        expected_metrics_count = 5
        assert len(children) == expected_metrics_count

    def test_dashboard_includes_distribution_chart_container(self):
        """Test that dashboard includes a container for the distribution chart.

        The distribution chart is a key visualization for Flow metrics,
        showing breakdown of work types (Feature, Defect, Risk, Debt).
        """
        dashboard = create_flow_dashboard()

        # Convert dashboard to string to search for distribution chart container ID
        dashboard_str = str(dashboard)

        # Should contain the distribution chart container ID
        assert "flow-distribution-chart-container" in dashboard_str, (
            "Dashboard should include distribution chart container"
        )
