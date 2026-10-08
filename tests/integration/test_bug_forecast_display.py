from data.bug_processing import forecast_bug_resolution
from ui.bug_analysis import create_bug_forecast_card


class TestBugForecastDisplay:
    def test_forecast_card_with_normal_data(self):
        weekly_stats = [
            {"week_start": "2025-01-01", "bugs_resolved": 5, "bugs_opened": 3},
            {"week_start": "2025-01-08", "bugs_resolved": 6, "bugs_opened": 4},
            {"week_start": "2025-01-15", "bugs_resolved": 4, "bugs_opened": 2},
            {"week_start": "2025-01-22", "bugs_resolved": 5, "bugs_opened": 1},
        ]

        forecast = forecast_bug_resolution(10, weekly_stats)
        forecast_card = create_bug_forecast_card(forecast, 10)

        assert forecast_card is not None
        assert hasattr(forecast_card, "children")

    def test_forecast_card_with_zero_bugs(self):
        weekly_stats = [
            {"week_start": "2025-01-01", "bugs_resolved": 5, "bugs_opened": 3},
        ]

        forecast = forecast_bug_resolution(0, weekly_stats)
        forecast_card = create_bug_forecast_card(forecast, 0)

        assert forecast_card is not None

    def test_forecast_card_with_insufficient_data(self):
        weekly_stats = [
            {"week_start": "2025-01-01", "bugs_resolved": 5, "bugs_opened": 3},
        ]

        forecast = forecast_bug_resolution(10, weekly_stats)
        forecast_card = create_bug_forecast_card(forecast, 10)

        assert forecast_card is not None
        assert forecast.get("insufficient_data") is True

    def test_forecast_card_date_formatting(self):
        weekly_stats = [
            {"week_start": "2025-01-01", "bugs_resolved": 5, "bugs_opened": 3},
            {"week_start": "2025-01-08", "bugs_resolved": 6, "bugs_opened": 4},
            {"week_start": "2025-01-15", "bugs_resolved": 4, "bugs_opened": 2},
            {"week_start": "2025-01-22", "bugs_resolved": 5, "bugs_opened": 1},
        ]

        forecast = forecast_bug_resolution(10, weekly_stats)
        _ = create_bug_forecast_card(forecast, 10)

        assert forecast.get("optimistic_date")
        assert forecast.get("most_likely_date")
        assert forecast.get("pessimistic_date")

        from datetime import datetime

        for date_field in ["optimistic_date", "most_likely_date", "pessimistic_date"]:
            iso_date = forecast.get(date_field)
            if iso_date:
                parsed = datetime.fromisoformat(iso_date)
                assert parsed is not None

    def test_forecast_card_shows_all_scenarios(self):
        weekly_stats = [
            {"week_start": "2025-01-01", "bugs_resolved": 5, "bugs_opened": 3},
            {"week_start": "2025-01-08", "bugs_resolved": 6, "bugs_opened": 4},
            {"week_start": "2025-01-15", "bugs_resolved": 4, "bugs_opened": 2},
            {"week_start": "2025-01-22", "bugs_resolved": 5, "bugs_opened": 1},
        ]

        forecast = forecast_bug_resolution(10, weekly_stats)
        _ = create_bug_forecast_card(forecast, 10)

        assert "optimistic_weeks" in forecast
        assert "most_likely_weeks" in forecast
        assert "pessimistic_weeks" in forecast

        assert forecast["optimistic_weeks"] <= forecast["most_likely_weeks"]
        assert forecast["most_likely_weeks"] <= forecast["pessimistic_weeks"]
