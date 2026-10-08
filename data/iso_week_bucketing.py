import logging
from datetime import date, datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


def get_iso_week_bounds(dt: datetime) -> tuple[date, date]:

    year, week, weekday = dt.isocalendar()

    monday = dt.date() - timedelta(days=weekday - 1)
    sunday = monday + timedelta(days=6)

    return monday, sunday


def get_week_label(dt: datetime) -> str:

    year, week, _ = dt.isocalendar()
    return f"{year}-W{week:02d}"


def get_last_n_weeks(
    n: int, end_date: datetime | None = None
) -> list[tuple[str, date, date]]:

    if end_date is None:
        end_date = datetime.now()

    weeks = []
    current_date = end_date

    for _i in range(n):
        monday, sunday = get_iso_week_bounds(current_date)
        week_label = get_week_label(current_date)

        weeks.append((week_label, monday, sunday))

        current_date = current_date - timedelta(days=7)

    return list(reversed(weeks))


def get_weeks_from_date_range(
    start_date: datetime, end_date: datetime
) -> list[tuple[str, date, date]]:

    weeks = []
    seen_labels = set()

    current = start_date
    while current <= end_date:
        monday, sunday = get_iso_week_bounds(current)
        week_label = get_week_label(current)

        if week_label not in seen_labels:
            seen_labels.add(week_label)
            weeks.append((week_label, monday, sunday))

        current = current + timedelta(days=7)

    end_week_label = get_week_label(end_date)
    if end_week_label not in seen_labels:
        monday, sunday = get_iso_week_bounds(end_date)
        weeks.append((end_week_label, monday, sunday))

    return weeks


def bucket_issues_by_week(
    issues: list[dict[str, Any]], date_field: str, n_weeks: int = 12
) -> dict[str, list[dict[str, Any]]]:

    weeks = get_last_n_weeks(n_weeks)
    week_ranges = {label: (monday, sunday) for label, monday, sunday in weeks}

    buckets: dict[str, list[dict[str, Any]]] = {
        label: [] for label in week_ranges.keys()
    }

    for issue in issues:
        date_value = issue.get(date_field)
        if not date_value and date_field == "resolutiondate":
            date_value = issue.get("resolved")
        if not date_value:
            date_value = issue.get("fields", {}).get(date_field)

        if not date_value:
            continue

        try:
            if "T" in date_value:
                issue_date = datetime.fromisoformat(
                    date_value.replace("Z", "+00:00")
                ).date()
            else:
                issue_date = datetime.fromisoformat(date_value).date()
        except (ValueError, AttributeError) as e:
            logger.warning(
                f"Could not parse date {date_value} "
                f"for issue {issue.get('key', 'unknown')}: {e}"
            )
            continue

        for week_label, (monday, sunday) in week_ranges.items():
            if monday <= issue_date <= sunday:
                buckets[week_label].append(issue)
                break

    return buckets


def get_week_range_description(n_weeks: int) -> str:

    weeks = get_last_n_weeks(n_weeks)
    if not weeks:
        return "No weeks"

    first_week = weeks[0][0]
    last_week = weeks[-1][0]

    return f"Last {n_weeks} weeks ({first_week} to {last_week})"
