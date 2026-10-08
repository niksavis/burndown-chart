from datetime import datetime


def get_current_iso_week() -> str:

    now = datetime.now()
    iso_calendar = now.isocalendar()
    return f"{iso_calendar.year}-W{iso_calendar.week:02d}"
