import dash_bootstrap_components as dbc
import pytest

from ui.dora_metrics_dashboard import (
    create_dora_dashboard,
    create_dora_loading_cards_grid,
    format_dora_metrics_for_display,
)


class TestCreateDoraDashboard:
    def test_dashboard_returns_container(self):
        dashboard = create_dora_dashboard()
        assert isinstance(dashboard, dbc.Container)

    def test_dashboard_has_children(self):
        dashboard = create_dora_dashboard()
        assert hasattr(dashboard, "children")
        children = dashboard.children
        assert children is not None
        assert len(children) > 0


class TestCreateDoraLoadingCardsGrid:
    def test_loading_cards_returns_row(self):
        loading_grid = create_dora_loading_cards_grid()
        assert isinstance(loading_grid, dbc.Row)

    def test_loading_cards_has_four_metrics(self):
        loading_grid = create_dora_loading_cards_grid()
        assert hasattr(loading_grid, "children")
        children = loading_grid.children
        assert children is not None
        assert len(children) == 4

    def test_loading_cards_use_columns(self):
        loading_grid = create_dora_loading_cards_grid()
        children = loading_grid.children
        assert children is not None
        for child in children:
            assert isinstance(child, dbc.Col)


class TestFormatDoraMetricsForDisplay:
    def test_format_returns_dict(self):
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

        assert "deployment_frequency" in result
        assert "lead_time_for_changes" in result
        assert "change_failure_rate" in result
        assert "mean_time_to_recovery" in result


class TestDashboardIntegration:
    def test_dashboard_can_be_created_without_errors(self):
        try:
            dashboard = create_dora_dashboard()
            assert dashboard is not None
        except Exception as e:
            pytest.fail(f"Dashboard creation raised exception: {e}")

    def test_loading_cards_match_metrics_count(self):
        loading_grid = create_dora_loading_cards_grid()
        children = loading_grid.children
        assert children is not None

        expected_metrics_count = 4
        assert len(children) == expected_metrics_count
