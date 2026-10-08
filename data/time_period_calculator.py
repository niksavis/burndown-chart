import logging
from datetime import date, datetime, timedelta

logger = logging.getLogger(__name__)


def get_iso_week(dt: datetime) -> tuple[int, int]:

    if not dt:
        logger.warning("get_iso_week called with None datetime, returning (0, 0)")
        return (0, 0)

    try:
        iso_calendar = dt.isocalendar()
        return (iso_calendar.year, iso_calendar.week)
    except AttributeError:
        logger.error(f"get_iso_week failed for {dt}, returning (0, 0)")
        return (0, 0)


def format_year_week(year: int, week: int) -> str:

    if not year or not week:
        logger.warning(
            f"format_year_week called with invalid values: year={year}, week={week}"
        )
        return "0000-W00"

    return f"{year}-W{week:02d}"


def get_year_week_label(dt: datetime) -> str:

    if not dt:
        logger.warning("get_year_week_label called with None datetime")
        return "0000-W00"

    year, week = get_iso_week(dt)
    return format_year_week(year, week)


def parse_year_week_label(label: str) -> tuple[int, int]:

    if not label or "-" not in label:
        logger.warning(f"parse_year_week_label called with invalid label: {label}")
        return (0, 0)

    try:
        parts = label.split("-")
        year = int(parts[0])
        week_str = parts[1].lstrip("W")
        week = int(week_str)
        return (year, week)
    except (ValueError, IndexError) as e:
        logger.error(f"Failed to parse year-week label '{label}': {e}")
        return (0, 0)


def get_week_start_date(year: int, week: int) -> date:

    if not year or not week:
        logger.warning(
            f"get_week_start_date called with invalid values: year={year}, week={week}"
        )
        return date.today()

    try:
        jan_4 = date(year, 1, 4)
        week_1_monday = jan_4 - timedelta(days=jan_4.weekday())
        target_monday = week_1_monday + timedelta(weeks=week - 1)
        return target_monday
    except (ValueError, OverflowError) as e:
        logger.error(f"Failed to calculate week start date for {year}-W{week}: {e}")
        return date.today()


def get_week_end_date(year: int, week: int) -> date:

    if not year or not week:
        logger.warning(
            f"get_week_end_date called with invalid values: year={year}, week={week}"
        )
        return date.today()

    try:
        monday = get_week_start_date(year, week)
        sunday = monday + timedelta(days=6)
        return sunday
    except (ValueError, OverflowError) as e:
        logger.error(f"Failed to calculate week end date for {year}-W{week}: {e}")
        return date.today()


def is_current_week(year: int, week: int) -> bool:

    if not year or not week:
        return False

    current_year, current_week = get_iso_week(datetime.now())
    return year == current_year and week == current_week


def generate_week_range(
    start_date: date, end_date: date, include_partial_current: bool = True
) -> list[str]:

    if not start_date or not end_date:
        logger.warning("generate_week_range called with None dates")
        return []

    if start_date > end_date:
        logger.warning(
            f"generate_week_range: start_date {start_date} > end_date {end_date}"
        )
        return []

    try:
        week_labels = []
        current_date = start_date

        while current_date <= end_date:
            year, week = get_iso_week(
                datetime.combine(current_date, datetime.min.time())
            )
            label = format_year_week(year, week)

            if label not in week_labels:
                if is_current_week(year, week):
                    if include_partial_current:
                        week_labels.append(label)
                else:
                    week_labels.append(label)

            current_date += timedelta(days=7)

        logger.info(
            f"Generated {len(week_labels)} weeks from {start_date} to {end_date}"
        )
        return week_labels

    except (ValueError, OverflowError) as e:
        logger.error(f"Failed to generate week range: {e}")
        return []


def get_recent_weeks(num_weeks: int, include_partial_current: bool = True) -> list[str]:

    if num_weeks <= 0:
        logger.warning(f"get_recent_weeks called with invalid num_weeks: {num_weeks}")
        return []

    try:
        today = date.today()
        start_date = today - timedelta(weeks=num_weeks - 1)

        return generate_week_range(start_date, today, include_partial_current)

    except (ValueError, OverflowError) as e:
        logger.error(f"Failed to get recent weeks: {e}")
        return []


def filter_by_week_range(
    items: list[dict], date_field: str, week_labels: list[str]
) -> list[dict]:

    if not items:
        return []

    if not week_labels:
        logger.warning("filter_by_week_range called with empty week_labels")
        return items

    try:
        filtered_items = []

        for item in items:
            date_value = item.get(date_field)
            if not date_value:
                logger.debug(
                    "Item missing date field "
                    f"'{date_field}': {item.get('key', 'unknown')}"
                )
                continue

            if isinstance(date_value, str):
                try:
                    dt = datetime.fromisoformat(date_value.replace("Z", "+00:00"))
                except ValueError:
                    logger.warning(
                        f"Failed to parse date '{date_value}' "
                        f"for item {item.get('key', 'unknown')}"
                    )
                    continue
            elif isinstance(date_value, datetime):
                dt = date_value
            elif isinstance(date_value, date):
                dt = datetime.combine(date_value, datetime.min.time())
            else:
                logger.warning(
                    "Unsupported date type "
                    f"{type(date_value)} for item {item.get('key', 'unknown')}"
                )
                continue

            item_week_label = get_year_week_label(dt)
            if item_week_label in week_labels:
                filtered_items.append(item)

        logger.info(
            f"Filtered {len(items)} items to {len(filtered_items)} items "
            f"in {len(week_labels)} weeks"
        )
        return filtered_items

    except Exception as e:
        logger.error(f"Failed to filter by week range: {e}")
        return items


def group_by_week(items: list[dict], date_field: str) -> dict[str, list[dict]]:

    if not items:
        return {}

    try:
        grouped = {}

        for item in items:
            date_value = item.get(date_field)
            if not date_value:
                logger.debug(
                    "Item missing date field "
                    f"'{date_field}': {item.get('key', 'unknown')}"
                )
                continue

            if isinstance(date_value, str):
                try:
                    dt = datetime.fromisoformat(date_value.replace("Z", "+00:00"))
                except ValueError:
                    logger.warning(
                        f"Failed to parse date '{date_value}' "
                        f"for item {item.get('key', 'unknown')}"
                    )
                    continue
            elif isinstance(date_value, datetime):
                dt = date_value
            elif isinstance(date_value, date):
                dt = datetime.combine(date_value, datetime.min.time())
            else:
                logger.warning(
                    "Unsupported date type "
                    f"{type(date_value)} for item {item.get('key', 'unknown')}"
                )
                continue

            week_label = get_year_week_label(dt)
            if week_label not in grouped:
                grouped[week_label] = []
            grouped[week_label].append(item)

        logger.info(f"Grouped {len(items)} items into {len(grouped)} weeks")
        return grouped

    except Exception as e:
        logger.error(f"Failed to group by week: {e}")
        return {}


MONDAY = 0
TUESDAY = 1
WEDNESDAY = 2
THURSDAY = 3
FRIDAY = 4
SATURDAY = 5
SUNDAY = 6
