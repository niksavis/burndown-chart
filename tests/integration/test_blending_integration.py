from datetime import datetime
from unittest.mock import patch

import pytest


class TestBlendingIntegration:
    @pytest.fixture
    def sample_weekly_values(self) -> list[float]:
        return [10.0, 11.0, 12.0, 13.0, 2.0]

    @pytest.fixture
    def mock_snapshots(self, sample_weekly_values) -> dict:
        snapshots = {}
        week_labels = ["2026-W06", "2026-W07", "2026-W08", "2026-W09", "2026-W10"]

        for i, week in enumerate(week_labels):
            snapshots[week] = {
                "flow_velocity": {
                    "completed_count": sample_weekly_values[i],
                    "metric_value": sample_weekly_values[i],
                }
            }
        return snapshots

    def test_monday_stability_no_cliff(self, sample_weekly_values, mock_snapshots):
        from data.metrics.blending import calculate_current_week_blend
        from data.metrics_calculator import calculate_forecast

        monday = datetime(2026, 2, 9, 10, 0)

        prior_weeks = sample_weekly_values[:-1]
        forecast_data = calculate_forecast(prior_weeks)
        assert forecast_data is not None, "Forecast calculation failed"
        forecast_value = forecast_data["forecast_value"]

        with patch("data.metrics.blending.datetime") as mock_datetime:
            mock_datetime.now.return_value = monday
            blended_monday = calculate_current_week_blend(0, forecast_value)

        assert blended_monday == pytest.approx(12.0, abs=0.1), (
            "Monday should show stable forecast"
        )
        assert blended_monday > 8.0, (
            "Monday value should be >8.0 (no 25% drop from 11.2)"
        )

    def test_week_progression_smooth(self, sample_weekly_values):
        from data.metrics.blending import calculate_current_week_blend
        from data.metrics_calculator import calculate_forecast

        prior_weeks = sample_weekly_values[:-1]
        forecast_data = calculate_forecast(prior_weeks)
        assert forecast_data is not None, "Forecast calculation failed"
        forecast_value = forecast_data["forecast_value"]

        test_cases = [
            (datetime(2026, 2, 9, 10, 0), 0, 12.0),
            (
                datetime(2026, 2, 10, 10, 0),
                2,
                10.0,
            ),
            (
                datetime(2026, 2, 11, 10, 0),
                5,
                9.2,
            ),
            (
                datetime(2026, 2, 12, 10, 0),
                8,
                9.6,
            ),
            (datetime(2026, 2, 13, 10, 0), 10, 10.4),
        ]

        results = []
        for test_time, actual, expected in test_cases:
            with patch("data.metrics.blending.datetime") as mock_datetime:
                mock_datetime.now.return_value = test_time
                blended = calculate_current_week_blend(actual, forecast_value)
                results.append(blended)

                assert blended == pytest.approx(expected, abs=0.05), (
                    f"{test_time.strftime('%A')}: Expected {expected}, got {blended}"
                )

        for i in range(len(results) - 1):
            diff = abs(results[i] - results[i + 1])
            assert diff < 5.0, (
                f"Large jump detected: {results[i]:.2f} → {results[i + 1]:.2f}"
            )

    def test_metadata_generation(self):
        from data.metrics.blending import get_blend_metadata

        wednesday = datetime(2026, 2, 11, 10, 0)

        with patch("data.metrics.blending.datetime") as mock_datetime:
            mock_datetime.now.return_value = wednesday
            metadata = get_blend_metadata(5.0, 11.5)

        required_keys = [
            "blended",
            "forecast",
            "actual",
            "actual_weight",
            "forecast_weight",
            "actual_percent",
            "forecast_percent",
            "weekday",
            "day_name",
            "is_blended",
        ]

        for key in required_keys:
            assert key in metadata, f"Missing key: {key}"

        assert metadata["day_name"] == "Wednesday"
        assert metadata["weekday"] == 2
        assert metadata["actual_percent"] == 40
        assert metadata["forecast_percent"] == 60
        assert metadata["is_blended"] is True

    def test_blend_description_format(self):
        from data.metrics.blending import format_blend_description, get_blend_metadata

        tuesday = datetime(2026, 2, 10, 10, 0)

        with patch("data.metrics.blending.datetime") as mock_datetime:
            mock_datetime.now.return_value = tuesday
            metadata = get_blend_metadata(2.0, 11.5)
            description = format_blend_description(metadata)

        assert "20%" in description or "20.0%" in description
        assert "80%" in description or "80.0%" in description
        assert "Tuesday" in description

    def test_weekend_no_blending(self):
        from data.metrics.blending import (
            calculate_current_week_blend,
            get_blend_metadata,
        )

        saturday = datetime(2026, 2, 14, 10, 0)

        with patch("data.metrics.blending.datetime") as mock_datetime:
            mock_datetime.now.return_value = saturday
            blended = calculate_current_week_blend(8.0, 11.5)
            metadata = get_blend_metadata(8.0, 11.5)

        assert blended == 8.0
        assert metadata["is_blended"] is False
        assert metadata["actual_percent"] == 100.0
        assert metadata["forecast_percent"] == 0.0

    def test_zero_forecast_handling(self):
        from data.metrics.blending import calculate_current_week_blend

        wednesday = datetime(2026, 2, 11, 10, 0)

        with patch("data.metrics.blending.datetime") as mock_datetime:
            mock_datetime.now.return_value = wednesday
            blended = calculate_current_week_blend(5.0, 0.0)

        assert blended == 2.0


class TestProcessingIntegration:
    pass


class TestUIIntegration:
    def test_blend_section_display(self):
        from ui.metric_cards import create_metric_card

        metric_data = {
            "metric_name": "flow_velocity",
            "value": 9.6,
            "unit": "items/week",
            "performance_tier": "Good",
            "performance_tier_color": "green",
            "error_state": "success",
            "total_issue_count": 50,
            "weekly_labels": [
                "2026-W06",
                "2026-W07",
                "2026-W08",
                "2026-W09",
                "2026-W10",
            ],
            "weekly_values": [10.0, 11.0, 12.0, 13.0, 9.6],
            "blend_metadata": {
                "blended": 9.6,
                "forecast": 11.5,
                "actual": 2.0,
                "actual_weight": 0.2,
                "forecast_weight": 0.8,
                "actual_percent": 20.0,
                "forecast_percent": 80.0,
                "weekday": 1,
                "day_name": "Tuesday",
                "is_blended": True,
            },
        }

        card = create_metric_card(metric_data, card_id="test-velocity-card")

        assert card is not None
        assert hasattr(card, "children")

    def test_no_blend_section_when_not_blended(self):
        from ui.metric_cards import create_metric_card

        metric_data = {
            "metric_name": "flow_velocity",
            "value": 10.0,
            "unit": "items/week",
            "performance_tier": "Good",
            "performance_tier_color": "green",
            "error_state": "success",
            "total_issue_count": 50,
            "weekly_labels": [
                "2026-W06",
                "2026-W07",
                "2026-W08",
                "2026-W09",
                "2026-W10",
            ],
            "weekly_values": [10.0, 11.0, 12.0, 13.0, 10.0],
            "blend_metadata": {
                "blended": 10.0,
                "forecast": 11.5,
                "actual": 10.0,
                "actual_weight": 1.0,
                "forecast_weight": 0.0,
                "actual_percent": 100.0,
                "forecast_percent": 0.0,
                "weekday": 5,
                "day_name": "Saturday",
                "is_blended": False,
            },
        }

        card = create_metric_card(metric_data, card_id="test-velocity-card-weekend")

        assert card is not None

    def test_detailed_chart_includes_adjusted_line(self):
        from ui.metric_cards import _create_detailed_chart

        weekly_labels = [
            "2026-W06",
            "2026-W07",
            "2026-W08",
            "2026-W09",
            "2026-W10",
        ]
        weekly_values = [10.0, 11.0, 12.0, 13.0, 2.0]
        weekly_values_adjusted = [10.0, 11.0, 12.0, 13.0, 9.6]
        metric_data = {
            "metric_name": "flow_velocity",
            "unit": "items/week",
            "performance_tier_color": "green",
        }

        chart = _create_detailed_chart(
            metric_name="flow_velocity",
            display_name="Flow Velocity",
            weekly_labels=weekly_labels,
            weekly_values=weekly_values,
            weekly_values_adjusted=weekly_values_adjusted,
            metric_data=metric_data,
            sparkline_color="#198754",
        )

        figure = chart.figure
        assert figure is not None
        assert len(figure["data"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
