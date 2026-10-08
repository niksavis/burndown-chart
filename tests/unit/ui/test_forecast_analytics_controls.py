from datetime import datetime

from ui.dashboard.forecast_analytics_controls import calculate_schedule_status


def test_calculate_schedule_status_treats_deadline_day_as_on_schedule() -> None:
    current_date = datetime(2026, 5, 1)

    status = calculate_schedule_status(
        forecast_date_str="2026-05-10",
        deadline_date_str="2026-05-10",
        current_date=current_date,
    )

    assert status["badge_text"] == "On Schedule"
    assert status["status"] == "ahead"
    assert status["percentage"] == 100


def test_calculate_schedule_status_clamps_negative_percentage_to_zero() -> None:
    current_date = datetime(2026, 5, 1)

    status = calculate_schedule_status(
        forecast_date_str="2026-04-20",
        deadline_date_str="2026-05-10",
        current_date=current_date,
    )

    assert status["percentage"] == 0
    assert status["bar_width"] == 0
