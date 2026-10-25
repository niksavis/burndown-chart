from datetime import datetime

from utils.business_time import business_now


def get_current_iso_week() -> str:

    now = business_now(
        datetime,
    )
    iso_calendar = now.isocalendar()
    return f"{iso_calendar.year}-W{iso_calendar.week:02d}"
