from unittest.mock import patch

import pytest

from callbacks.settings.helpers import calculate_remaining_work_for_data_window


class TestDataPointsSliderRemainingFixed:
    @pytest.fixture
    def mock_statistics(self):
        statistics = []
        for week in range(12, 0, -1):
            statistics.append(
                {
                    "date": f"2026-01-{7 - (week // 4):02d}",
                    "week_label": f"2026-W{1 + (12 - week):02d}",
                    "completed_items": 10,
                    "completed_points": 50.0,
                }
            )
        return statistics

    @pytest.fixture
    def mock_project_scope(self):
        return {
            "total_items": 260,
            "completed_items": 123,
            "remaining_items": 137,
            "estimated_items": 137,
            "estimated_points": 848.0,
            "remaining_total_points": 848.0,
            "completed_points": 615.0,
        }

    def test_slider_at_12_weeks_shows_current_remaining(
        self, mock_statistics, mock_project_scope
    ):

        with patch("callbacks.settings.helpers.load_unified_project_data") as mock_load:
            mock_load.return_value = {"project_scope": mock_project_scope}

            result = calculate_remaining_work_for_data_window(
                data_points_count=12, statistics=mock_statistics
            )

            assert result is not None, "Should return calculation result"
            (
                estimated_items,
                remaining_items,
                estimated_points,
                remaining_points_str,
                calc_results,
            ) = result

            assert remaining_items == 137, (
                f"Expected 137 remaining items (current), got {remaining_items}"
            )

            remaining_points = float(remaining_points_str)
            assert remaining_points == 848.0, (
                f"Expected 848.0 remaining points (current), got {remaining_points}"
            )

    def test_slider_at_4_weeks_shows_current_remaining(
        self, mock_statistics, mock_project_scope
    ):

        with patch("callbacks.settings.helpers.load_unified_project_data") as mock_load:
            mock_load.return_value = {"project_scope": mock_project_scope}

            result = calculate_remaining_work_for_data_window(
                data_points_count=4, statistics=mock_statistics
            )

            assert result is not None, "Should return calculation result"
            (
                estimated_items,
                remaining_items,
                estimated_points,
                remaining_points_str,
                calc_results,
            ) = result

            assert remaining_items == 137, (
                f"Expected 137 remaining items (current), got {remaining_items}"
            )

            remaining_points = float(remaining_points_str)
            assert remaining_points == 848.0, (
                f"Expected 848.0 remaining points (current), got {remaining_points}"
            )

    def test_slider_change_does_not_affect_remaining(
        self, mock_statistics, mock_project_scope
    ):

        with patch("callbacks.settings.helpers.load_unified_project_data") as mock_load:
            mock_load.return_value = {"project_scope": mock_project_scope}

            result_4w = calculate_remaining_work_for_data_window(
                data_points_count=4, statistics=mock_statistics
            )

            result_12w = calculate_remaining_work_for_data_window(
                data_points_count=12, statistics=mock_statistics
            )

            assert result_4w is not None and result_12w is not None

            _, remaining_items_4w, _, remaining_points_4w_str, _ = result_4w
            _, remaining_items_12w, _, remaining_points_12w_str, _ = result_12w

            remaining_points_4w = float(remaining_points_4w_str)
            remaining_points_12w = float(remaining_points_12w_str)

            assert remaining_items_12w == remaining_items_4w, (
                "Remaining items should be the same: "
                f"12w={remaining_items_12w}, 4w={remaining_items_4w}"
            )

            assert remaining_points_12w == remaining_points_4w, (
                "Remaining points should be the same: "
                f"12w={remaining_points_12w}, 4w={remaining_points_4w}"
            )

    def test_avg_points_per_item_calculated(self, mock_statistics, mock_project_scope):

        with patch("callbacks.settings.helpers.load_unified_project_data") as mock_load:
            mock_load.return_value = {"project_scope": mock_project_scope}

            result = calculate_remaining_work_for_data_window(
                data_points_count=8, statistics=mock_statistics
            )

            assert result is not None
            _, _, _, _, calc_results = result

            avg = calc_results.get("avg_points_per_item", 0)
            assert avg > 0, (
                "avg_points_per_item should be calculated from current remaining"
            )

            expected_avg = 848.0 / 137
            assert abs(avg - expected_avg) < 0.01, (
                f"Expected avg ~{expected_avg} points/item, got {avg}"
            )

    def test_with_no_data_points_count_returns_none(
        self, mock_statistics, mock_project_scope
    ):
        with patch("callbacks.settings.helpers.load_unified_project_data") as mock_load:
            mock_load.return_value = {"project_scope": mock_project_scope}

            result = calculate_remaining_work_for_data_window(
                data_points_count=None, statistics=mock_statistics
            )

            assert result is None, "Should return None when data_points_count is None"

    def test_returns_current_scope_always(self, mock_project_scope):

        limited_statistics = [
            {
                "date": "2026-01-06",
                "week_label": "2026-W01",
                "completed_items": 10,
                "completed_points": 50.0,
            },
            {
                "date": "2026-01-07",
                "week_label": "2026-W02",
                "completed_items": 10,
                "completed_points": 50.0,
            },
        ]

        with patch("callbacks.settings.helpers.load_unified_project_data") as mock_load:
            mock_load.return_value = {"project_scope": mock_project_scope}

            result = calculate_remaining_work_for_data_window(
                data_points_count=12, statistics=limited_statistics
            )

            assert result is not None
            (
                estimated_items,
                remaining_items,
                estimated_points,
                remaining_points_str,
                _,
            ) = result

            assert estimated_items == mock_project_scope["estimated_items"]
            assert remaining_items == mock_project_scope["remaining_items"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
