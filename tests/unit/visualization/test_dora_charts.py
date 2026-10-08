from datetime import datetime, timedelta

from visualization.dora_charts import (
    create_deployment_frequency_chart,
    create_deployment_frequency_trend,
    create_lead_time_chart,
    create_lead_time_trend,
)


class TestCreateDeploymentFrequencyTrend:
    def test_trend_chart_with_valid_data(self):
        base_date = datetime(2025, 1, 1)
        trend_data = [
            {
                "date": (base_date + timedelta(days=i * 7)).isoformat(),
                "value": 25 + i * 2,
            }
            for i in range(8)
        ]

        metric_data = {
            "value": 39.0,
            "performance_tier": "Elite",
            "performance_tier_color": "green",
        }

        figure = create_deployment_frequency_trend(trend_data, metric_data)

        assert figure is not None
        assert len(figure.data) > 0  # type: ignore[arg-type]  # Should have at least one trace

        assert figure.data[0].type == "scatter"  # type: ignore[union-attr]
        assert figure.data[0].mode == "lines+markers"  # type: ignore[union-attr]

    def test_trend_chart_with_empty_data(self):
        trend_data = []
        metric_data = {"value": 0, "performance_tier": "Low"}

        figure = create_deployment_frequency_trend(trend_data, metric_data)

        assert figure is not None
        assert len(figure.layout.annotations) > 0  # type: ignore[union-attr]  # Should have "no data" message

    def test_trend_chart_with_single_data_point(self):
        trend_data = [{"date": "2025-01-01", "value": 30.5}]
        metric_data = {"value": 30.5, "performance_tier": "Elite"}

        figure = create_deployment_frequency_trend(trend_data, metric_data)

        assert figure is not None
        assert len(figure.data) > 0  # type: ignore[arg-type]


class TestCreateLeadTimeTrend:
    def test_trend_chart_with_valid_data(self):
        base_date = datetime(2025, 1, 1)
        trend_data = [
            {
                "date": (base_date + timedelta(days=i * 7)).isoformat(),
                "value": 5.0 - i * 0.3,
            }
            for i in range(8)
        ]

        metric_data = {
            "value": 2.9,
            "performance_tier": "High",
            "performance_tier_color": "yellow",
        }

        figure = create_lead_time_trend(trend_data, metric_data)

        assert figure is not None
        assert len(figure.data) > 0  # type: ignore[arg-type]

        assert figure.data[0].type == "scatter"  # type: ignore[union-attr]
        assert figure.data[0].mode == "lines+markers"  # type: ignore[union-attr]

    def test_trend_chart_with_empty_data(self):
        trend_data = []
        metric_data = {"value": 0, "performance_tier": "Low"}

        figure = create_lead_time_trend(trend_data, metric_data)

        assert figure is not None
        assert len(figure.layout.annotations) > 0  # type: ignore[union-attr]


class TestExistingChartFunctions:
    def test_deployment_frequency_chart_current_value(self):
        metric_data = {
            "value": 35.0,
            "unit": "per month",
            "performance_tier": "Elite",
            "performance_tier_color": "green",
        }

        figure = create_deployment_frequency_chart(metric_data)

        assert figure is not None
        assert len(figure.data) > 0  # type: ignore[arg-type]

    def test_deployment_frequency_chart_with_historical(self):
        metric_data = {
            "value": 35.0,
            "unit": "per month",
            "performance_tier": "Elite",
            "performance_tier_color": "green",
        }

        historical_data = [
            {"date": "2025-01-01", "value": 30.0},
            {"date": "2025-01-08", "value": 32.0},
            {"date": "2025-01-15", "value": 35.0},
        ]

        figure = create_deployment_frequency_chart(metric_data, historical_data)

        assert figure is not None
        assert len(figure.data) > 0  # type: ignore[arg-type]

    def test_lead_time_chart_current_value(self):
        metric_data = {
            "value": 2.5,
            "unit": "days",
            "performance_tier": "High",
            "performance_tier_color": "yellow",
        }

        figure = create_lead_time_chart(metric_data)

        assert figure is not None
        assert len(figure.data) > 0  # type: ignore[arg-type]


class TestTrendChartBenchmarks:
    def test_deployment_frequency_has_benchmark_lines(self):
        trend_data = [
            {"date": "2025-01-01", "value": 25.0},
            {"date": "2025-01-08", "value": 30.0},
            {"date": "2025-01-15", "value": 35.0},
        ]
        metric_data = {"value": 35.0, "performance_tier": "Elite"}

        figure = create_deployment_frequency_trend(trend_data, metric_data)

        assert figure.layout.shapes is not None  # type: ignore[union-attr]
        assert len(figure.layout.shapes) > 0  # type: ignore[union-attr]

    def test_lead_time_has_benchmark_lines(self):
        trend_data = [
            {"date": "2025-01-01", "value": 5.0},
            {"date": "2025-01-08", "value": 3.0},
            {"date": "2025-01-15", "value": 2.0},
        ]
        metric_data = {"value": 2.0, "performance_tier": "High"}

        figure = create_lead_time_trend(trend_data, metric_data)

        assert figure.layout.shapes is not None  # type: ignore[union-attr]
        assert len(figure.layout.shapes) > 0  # type: ignore[union-attr]
