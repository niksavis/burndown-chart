"""
Unit tests for metrics snapshot storage with forecast calculation (Feature 009).

Tests cover:
- save_metric_snapshot_with_forecast(): Enhanced metric saving with automatic forecast
- get_last_n_weeks_values(): Historical data retrieval for forecast calculation

Test organization follows TDD approach with isolated temporary file fixtures.
"""

import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch


class TestSaveMetricSnapshotWithForecast:
    """Tests for save_metric_snapshot_with_forecast() function."""

    @pytest.fixture
    def temp_snapshots_file(self):
        """Create isolated temporary file for testing - proper cleanup guaranteed."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            temp_file = f.name
            # Initialize with empty snapshots
            json.dump({}, f)

        yield temp_file

        # Cleanup - executes even if test fails
        if os.path.exists(temp_file):
            os.unlink(temp_file)

    @pytest.fixture
    def mock_snapshots_with_history(self, temp_snapshots_file):
        """Create snapshots with 4 weeks of historical Flow Velocity data."""
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
        """Test saving Flow Velocity metric with automatic forecast calculation."""
        from data.metrics_snapshots import save_metric_snapshot_with_forecast
        import json

        # Mock database save while preserving file writes
        def mock_save_to_file(snapshots_dict):
            with open(mock_snapshots_with_history, "w") as f:
                json.dump(snapshots_dict, f, indent=2)
            return True

        # Mock load to read from file instead of database
        def mock_load_from_file():
            with open(mock_snapshots_with_history, "r") as f:
                return json.load(f)

        # Mock database operations to prevent FOREIGN KEY errors
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
            # Save new week's data
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

            # Verify snapshot was saved with forecast
            with open(mock_snapshots_with_history, "r") as f:
                snapshots = json.load(f)

            assert "2025-W44" in snapshots
            assert "flow_velocity" in snapshots["2025-W44"]

            metric_snapshot = snapshots["2025-W44"]["flow_velocity"]

            # Verify base data
            assert metric_snapshot["completed_count"] == 15

            # Verify forecast was calculated
            assert "forecast" in metric_snapshot
            forecast = metric_snapshot["forecast"]
            assert "forecast_value" in forecast
            assert forecast["confidence"] in ["established", "building"]
            assert forecast["weeks_available"] == 4

            # Verify trend was calculated
            assert "trend_vs_forecast" in metric_snapshot
            trend = metric_snapshot["trend_vs_forecast"]
            assert "direction" in trend  # ↗, →, or ↘
            assert "deviation_percent" in trend
            assert "status_text" in trend

    def test_save_flow_load_with_range(self, mock_snapshots_with_history):
        """Test Flow Load metric includes forecast range calculation."""
        from data.metrics_snapshots import save_metric_snapshot_with_forecast
        import json

        # Add Flow Load historical data
        with open(mock_snapshots_with_history, "r") as f:
            snapshots = json.load(f)

        for week in ["2025-W40", "2025-W41", "2025-W42", "2025-W43"]:
            snapshots[week]["flow_load"] = {
                "wip_count": 12,
                "by_status": {"In Progress": 10, "In Review": 2},
            }

        with open(mock_snapshots_with_history, "w") as f:
            json.dump(snapshots, f)

        # Mock database save while preserving file writes
        def mock_save_to_file(snapshots_dict):
            with open(mock_snapshots_with_history, "w") as f:
                json.dump(snapshots_dict, f, indent=2)
            return True

        # Mock load to read from file instead of database
        def mock_load_from_file():
            with open(mock_snapshots_with_history, "r") as f:
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

            # Verify range was calculated
            with open(mock_snapshots_with_history, "r") as f:
                snapshots = json.load(f)

            metric_snapshot = snapshots["2025-W44"]["flow_load"]
            assert "forecast" in metric_snapshot
            assert "forecast_range" in metric_snapshot["forecast"]

            forecast_range = metric_snapshot["forecast"]["forecast_range"]
            assert "lower" in forecast_range
            assert "upper" in forecast_range
            # Check for optional optimal_range text (not part of range data)
            # assert "optimal_range" in forecast_range

    def test_insufficient_history_no_forecast(self, temp_snapshots_file):
        """Test that no forecast is calculated with insufficient history."""
        from data.metrics_snapshots import save_metric_snapshot_with_forecast
        import json

        # Create snapshot with NO existing weeks (only current week = 1 week total)
        # This is below min_weeks=2 threshold, so no forecast should be generated
        with open(temp_snapshots_file, "w") as f:
            json.dump({}, f)  # Empty history

        # Mock database save while preserving file writes
        def mock_save_to_file(snapshots_dict):
            with open(temp_snapshots_file, "w") as f:
                json.dump(snapshots_dict, f, indent=2)
            return True

        # Mock database load to return empty history
        def mock_load_from_file():
            with open(temp_snapshots_file, "r") as f:
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

            # Verify snapshot saved but no forecast (only 1 week, below min_weeks=2)
            with open(temp_snapshots_file, "r") as f:
                snapshots = json.load(f)

            metric_snapshot = snapshots["2025-W44"]["flow_velocity"]
            assert (
                "forecast" not in metric_snapshot
                or metric_snapshot.get("forecast") is None
            )

    def test_auto_detect_metric_type(self, mock_snapshots_with_history):
        """Test automatic detection of higher_better vs lower_better metrics."""
        from data.metrics_snapshots import save_metric_snapshot_with_forecast
        import json

        # Add historical data for DORA Lead Time (lower_better)
        with open(mock_snapshots_with_history, "r") as f:
            snapshots = json.load(f)

        for week in ["2025-W40", "2025-W41", "2025-W42", "2025-W43"]:
            snapshots[week]["dora_lead_time"] = {
                "median_hours": 24.0,
                "percentile_85": 48.0,
            }

        with open(mock_snapshots_with_history, "w") as f:
            json.dump(snapshots, f)

        # Mock database save while preserving file writes
        def mock_save_to_file(snapshots_dict):
            with open(mock_snapshots_with_history, "w") as f:
                json.dump(snapshots_dict, f, indent=2)
            return True

        # Mock load to read from file instead of database
        def mock_load_from_file():
            with open(mock_snapshots_with_history, "r") as f:
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
            # Don't provide metric_type - should auto-detect
            success = save_metric_snapshot_with_forecast(
                week_label="2025-W44",
                metric_name="dora_lead_time",
                metric_data={"median_hours": 20.0, "percentile_85": 40.0},
            )

            assert success is True

            # Verify trend was calculated with correct interpretation
            with open(mock_snapshots_with_history, "r") as f:
                snapshots = json.load(f)

            metric_snapshot = snapshots["2025-W44"]["dora_lead_time"]
            assert "trend_vs_forecast" in metric_snapshot

            # Lower value (20 vs 24 forecast) should be "good" for lower_better metric
            trend = metric_snapshot["trend_vs_forecast"]
            assert trend["is_good"] is True  # Lower is better for lead time


class TestGetLastNWeeksValues:
    """Tests for get_last_n_weeks_values() helper function."""

    @pytest.fixture
    def temp_snapshots_file(self):
        """Create isolated temporary file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            temp_file = f.name
            json.dump({}, f)

        yield temp_file

        if os.path.exists(temp_file):
            os.unlink(temp_file)

    def test_get_chronological_values(self, temp_snapshots_file):
        """Test retrieval of values in chronological order (oldest to newest)."""
        from data.metrics_snapshots import get_last_n_weeks_values

        # Create 6 weeks of data
        historical_data = {}
        for i, week in enumerate(
            ["2025-W40", "2025-W41", "2025-W42", "2025-W43", "2025-W44", "2025-W45"]
        ):
            historical_data[week] = {
                "flow_velocity": {
                    "completed_count": (i + 1) * 10  # 10, 20, 30, 40, 50, 60
                }
            }

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
            # Get last 4 weeks (should be weeks 42, 43, 44, 45 → values 30, 40, 50, 60)
            values = get_last_n_weeks_values(
                metric_key="flow_velocity", value_key="completed_count", n_weeks=4
            )

            assert values == [30, 40, 50, 60]  # Chronological order

    def test_exclude_current_week(self, temp_snapshots_file):
        """Test exclusion of current week from historical values."""
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
            # Get last 4 weeks but exclude current week (2025-W44)
            values = get_last_n_weeks_values(
                metric_key="flow_velocity",
                value_key="completed_count",
                n_weeks=4,
                current_week="2025-W44",
            )

            # Should get weeks 41, 42, 43 (not 44)
            assert values == [10, 20, 30]
            assert len(values) == 3
