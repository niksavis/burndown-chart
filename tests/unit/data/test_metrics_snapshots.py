import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


class TestSaveMetricSnapshotWithForecast:
    @pytest.fixture
    def temp_snapshots_file(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            temp_file = f.name
            json.dump({}, f)

        yield temp_file

        if os.path.exists(temp_file):
            os.unlink(temp_file)

    @pytest.fixture
    def mock_snapshots_with_history(self, temp_snapshots_file):
        historical_data = {
            "2025-W40": {
                "flow_velocity": {
                    "completed_count": 10,
                    "distribution": {"Feature": 8, "Bug": 2},
                    "timestamp": "2025-10-01T10:00:00Z",
                }
            },
            "2025-W41": {
                "flow_velocity": {
                    "completed_count": 12,
                    "distribution": {"Feature": 9, "Bug": 3},
                    "timestamp": "2025-10-08T10:00:00Z",
                }
            },
            "2025-W42": {
                "flow_velocity": {
                    "completed_count": 11,
                    "distribution": {"Feature": 10, "Bug": 1},
                    "timestamp": "2025-10-15T10:00:00Z",
                }
            },
            "2025-W43": {
                "flow_velocity": {
                    "completed_count": 13,
                    "distribution": {"Feature": 11, "Bug": 2},
                    "timestamp": "2025-10-22T10:00:00Z",
                }
            },
        }

        with open(temp_snapshots_file, "w") as f:
            json.dump(historical_data, f, indent=2)

        return temp_snapshots_file

    def test_save_flow_velocity_with_forecast(self, mock_snapshots_with_history):
        import json

        from data.metrics_snapshots import save_metric_snapshot_with_forecast

        def mock_save_to_file(snapshots_dict):
            with open(mock_snapshots_with_history, "w") as f:
                json.dump(snapshots_dict, f, indent=2)
            return True

        def mock_load_from_file():
            with open(mock_snapshots_with_history) as f:
                return json.load(f)

        with (
            patch(
                "data.metrics_snapshots.save_snapshots", side_effect=mock_save_to_file
            ),
            patch(
                "data.metrics_snapshots.load_snapshots", side_effect=mock_load_from_file
            ),
            patch(
                "data.metrics_snapshots._get_snapshots_file_path",
                return_value=Path(mock_snapshots_with_history),
            ),
        ):
            success = save_metric_snapshot_with_forecast(
                week_label="2025-W44",
                metric_name="flow_velocity",
                metric_data={
                    "completed_count": 15,
                    "distribution": {"Feature": 12, "Bug": 3},
                },
                metric_type="higher_better",
            )

            assert success is True

            with open(mock_snapshots_with_history) as f:
                snapshots = json.load(f)

            assert "2025-W44" in snapshots
            assert "flow_velocity" in snapshots["2025-W44"]

            metric_snapshot = snapshots["2025-W44"]["flow_velocity"]

            assert metric_snapshot["completed_count"] == 15

            assert "forecast" in metric_snapshot
            forecast = metric_snapshot["forecast"]
            assert "forecast_value" in forecast
            assert forecast["confidence"] in ["established", "building"]
            assert forecast["weeks_available"] == 4

            assert "trend_vs_forecast" in metric_snapshot
            trend = metric_snapshot["trend_vs_forecast"]
            assert "direction" in trend
            assert "deviation_percent" in trend
            assert "status_text" in trend

    def test_save_flow_load_with_range(self, mock_snapshots_with_history):
        import json

        from data.metrics_snapshots import save_metric_snapshot_with_forecast

        with open(mock_snapshots_with_history) as f:
            snapshots = json.load(f)

        for week in ["2025-W40", "2025-W41", "2025-W42", "2025-W43"]:
            snapshots[week]["flow_load"] = {
                "wip_count": 12,
                "by_status": {"In Progress": 10, "In Review": 2},
            }

        with open(mock_snapshots_with_history, "w") as f:
            json.dump(snapshots, f)

        def mock_save_to_file(snapshots_dict):
            with open(mock_snapshots_with_history, "w") as f:
                json.dump(snapshots_dict, f, indent=2)
            return True

        def mock_load_from_file():
            with open(mock_snapshots_with_history) as f:
                return json.load(f)

        with (
            patch(
                "data.metrics_snapshots.save_snapshots", side_effect=mock_save_to_file
            ),
            patch(
                "data.metrics_snapshots.load_snapshots", side_effect=mock_load_from_file
            ),
            patch(
                "data.metrics_snapshots._get_snapshots_file_path",
                return_value=Path(mock_snapshots_with_history),
            ),
        ):
            success = save_metric_snapshot_with_forecast(
                week_label="2025-W44",
                metric_name="flow_load",
                metric_data={
                    "wip_count": 14,
                    "by_status": {"In Progress": 12, "In Review": 2},
                },
            )

            assert success is True

            with open(mock_snapshots_with_history) as f:
                snapshots = json.load(f)

            metric_snapshot = snapshots["2025-W44"]["flow_load"]
            assert "forecast" in metric_snapshot
            assert "forecast_range" in metric_snapshot["forecast"]

            forecast_range = metric_snapshot["forecast"]["forecast_range"]
            assert "lower" in forecast_range
            assert "upper" in forecast_range

    def test_insufficient_history_no_forecast(self, temp_snapshots_file):
        import json

        from data.metrics_snapshots import save_metric_snapshot_with_forecast

        with open(temp_snapshots_file, "w") as f:
            json.dump({}, f)

        def mock_save_to_file(snapshots_dict):
            with open(temp_snapshots_file, "w") as f:
                json.dump(snapshots_dict, f, indent=2)
            return True

        def mock_load_from_file():
            with open(temp_snapshots_file) as f:
                return json.load(f)

        with (
            patch(
                "data.metrics_snapshots.save_snapshots", side_effect=mock_save_to_file
            ),
            patch(
                "data.metrics_snapshots.load_snapshots", side_effect=mock_load_from_file
            ),
            patch(
                "data.metrics_snapshots._get_snapshots_file_path",
                return_value=Path(temp_snapshots_file),
            ),
        ):
            success = save_metric_snapshot_with_forecast(
                week_label="2025-W44",
                metric_name="flow_velocity",
                metric_data={
                    "completed_count": 12,
                    "distribution": {"Feature": 10, "Bug": 2},
                },
                metric_type="higher_better",
            )

            assert success is True

            with open(temp_snapshots_file) as f:
                snapshots = json.load(f)

            metric_snapshot = snapshots["2025-W44"]["flow_velocity"]
            assert (
                "forecast" not in metric_snapshot
                or metric_snapshot.get("forecast") is None
            )

    def test_auto_detect_metric_type(self, mock_snapshots_with_history):
        import json

        from data.metrics_snapshots import save_metric_snapshot_with_forecast

        with open(mock_snapshots_with_history) as f:
            snapshots = json.load(f)

        for week in ["2025-W40", "2025-W41", "2025-W42", "2025-W43"]:
            snapshots[week]["dora_lead_time"] = {
                "median_hours": 24.0,
                "percentile_85": 48.0,
            }

        with open(mock_snapshots_with_history, "w") as f:
            json.dump(snapshots, f)

        def mock_save_to_file(snapshots_dict):
            with open(mock_snapshots_with_history, "w") as f:
                json.dump(snapshots_dict, f, indent=2)
            return True

        def mock_load_from_file():
            with open(mock_snapshots_with_history) as f:
                return json.load(f)

        with (
            patch(
                "data.metrics_snapshots.save_snapshots", side_effect=mock_save_to_file
            ),
            patch(
                "data.metrics_snapshots.load_snapshots", side_effect=mock_load_from_file
            ),
            patch(
                "data.metrics_snapshots._get_snapshots_file_path",
                return_value=Path(mock_snapshots_with_history),
            ),
        ):
            success = save_metric_snapshot_with_forecast(
                week_label="2025-W44",
                metric_name="dora_lead_time",
                metric_data={"median_hours": 20.0, "percentile_85": 40.0},
            )

            assert success is True

            with open(mock_snapshots_with_history) as f:
                snapshots = json.load(f)

            metric_snapshot = snapshots["2025-W44"]["dora_lead_time"]
            assert "trend_vs_forecast" in metric_snapshot

            trend = metric_snapshot["trend_vs_forecast"]
            assert trend["is_good"] is True


class TestGetLastNWeeksValues:
    @pytest.fixture
    def temp_snapshots_file(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            temp_file = f.name
            json.dump({}, f)

        yield temp_file

        if os.path.exists(temp_file):
            os.unlink(temp_file)

    def test_get_chronological_values(self, temp_snapshots_file):
        from data.metrics_snapshots import get_last_n_weeks_values

        historical_data = {}
        for i, week in enumerate(
            ["2025-W40", "2025-W41", "2025-W42", "2025-W43", "2025-W44", "2025-W45"]
        ):
            historical_data[week] = {"flow_velocity": {"completed_count": (i + 1) * 10}}

        with open(temp_snapshots_file, "w") as f:
            json.dump(historical_data, f)

        with (
            patch(
                "data.metrics_snapshots.load_snapshots", return_value=historical_data
            ),
            patch(
                "data.metrics_snapshots._get_snapshots_file_path",
                return_value=Path(temp_snapshots_file),
            ),
        ):
            values = get_last_n_weeks_values(
                metric_key="flow_velocity", value_key="completed_count", n_weeks=4
            )

            assert values == [30, 40, 50, 60]

    def test_exclude_current_week(self, temp_snapshots_file):
        from data.metrics_snapshots import get_last_n_weeks_values

        historical_data = {}
        for i, week in enumerate(["2025-W41", "2025-W42", "2025-W43", "2025-W44"]):
            historical_data[week] = {"flow_velocity": {"completed_count": (i + 1) * 10}}

        with open(temp_snapshots_file, "w") as f:
            json.dump(historical_data, f)

        with (
            patch(
                "data.metrics_snapshots.load_snapshots", return_value=historical_data
            ),
            patch(
                "data.metrics_snapshots._get_snapshots_file_path",
                return_value=Path(temp_snapshots_file),
            ),
        ):
            values = get_last_n_weeks_values(
                metric_key="flow_velocity",
                value_key="completed_count",
                n_weeks=4,
                current_week="2025-W44",
            )

            assert values == [10, 20, 30]
            assert len(values) == 3
