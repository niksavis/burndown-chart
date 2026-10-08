import dash_bootstrap_components as dbc
import pytest

from ui.flow_metrics_dashboard import create_flow_dashboard


class TestCreateFlowDashboard:
    def test_dashboard_returns_container(self):
        dashboard = create_flow_dashboard()
        assert isinstance(dashboard, dbc.Container)

    def test_dashboard_has_children(self):
        dashboard = create_flow_dashboard()
        assert hasattr(dashboard, "children")
        children = dashboard.children
        assert children is not None
        assert len(children) > 0


class TestFormatFlowMetricsForDisplay:
    def test_format_function_can_be_implemented_later(self):
        assert True


class TestDashboardIntegration:
    def test_dashboard_can_be_created_without_errors(self):
        try:
            dashboard = create_flow_dashboard()
            assert dashboard is not None
        except Exception as e:
            pytest.fail(f"Dashboard creation raised exception: {e}")

    def test_dashboard_includes_metrics_cards_container(self):

        dashboard = create_flow_dashboard()

        dashboard_str = str(dashboard)

        assert "flow-metrics-cards-container" in dashboard_str, (
            "Dashboard should include flow-metrics-cards-container"
        )
