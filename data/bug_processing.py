from datetime import datetime, timedelta

dt = datetime


def filter_bug_issues(
    issues: list[dict],
    bug_type_mappings: dict[str, str],
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[dict]:

    filtered_bugs = []

    for issue in issues:
        if "fields" in issue:
            issue_type = issue.get("fields", {}).get("issuetype", {}).get("name", "")
        else:
            issue_type = issue.get("issue_type", "")

        if issue_type not in bug_type_mappings:
            continue

        if date_from or date_to:
            if "fields" in issue:
                created_str = issue.get("fields", {}).get("created", "")
            else:
                created_str = issue.get("created", "")

            if created_str:
                try:
                    created_date = datetime.strptime(
                        created_str[:19], "%Y-%m-%dT%H:%M:%S"
                    )

                    if date_from and created_date < date_from:
                        continue
                    if date_to and created_date > date_to:
                        continue
                except ValueError:
                    continue

        filtered_bugs.append(issue)

    return filtered_bugs


def calculate_bug_statistics(
    bug_issues: list[dict],
    date_from: datetime,
    date_to: datetime,
    story_points_field: str = "customfield_10016",
) -> list[dict]:

    if not isinstance(bug_issues, list) or len(bug_issues) == 0:
        raise ValueError("Cannot calculate statistics from empty bug list")

    if not isinstance(date_from, datetime) or not isinstance(date_to, datetime):
        raise ValueError("date_from and date_to must be datetime objects")

    if date_from >= date_to:
        raise ValueError(f"date_from ({date_from}) must be before date_to ({date_to})")

    weekly_stats = {}

    start_week = get_iso_week(date_from)
    end_week = get_iso_week(date_to)

    year_start, week_start = map(int, start_week.split("-W"))
    year_end, week_end = map(int, end_week.split("-W"))

    for year in range(year_start, year_end + 1):
        start = week_start if year == year_start else 1
        max_week_in_year = get_max_iso_week_for_year(year)
        end = min(week_end if year == year_end else max_week_in_year, max_week_in_year)

        for week in range(start, end + 1):
            week_key = f"{year}-W{week:02d}"
            if week_key not in weekly_stats:
                weekly_stats[week_key] = {
                    "week": week_key,
                    "week_start_date": get_week_start_date(week_key),
                    "bugs_created": 0,
                    "bugs_resolved": 0,
                    "bugs_points_created": 0,
                    "bugs_points_resolved": 0,
                    "net_bugs": 0,
                    "net_points": 0,
                    "cumulative_open_bugs": 0,
                }

    for bug in bug_issues:
        created_str = bug.get("created", "")
        if created_str:
            try:
                created_date = datetime.strptime(created_str[:19], "%Y-%m-%dT%H:%M:%S")
                created_week = get_iso_week(created_date)

                if created_week in weekly_stats:
                    weekly_stats[created_week]["bugs_created"] += 1

                    points = bug.get("points") or 0
                    weekly_stats[created_week]["bugs_points_created"] += points

            except ValueError:
                continue

        resolved_str = bug.get("resolved")
        if resolved_str:
            try:
                resolved_date = datetime.strptime(
                    resolved_str[:19], "%Y-%m-%dT%H:%M:%S"
                )
                resolved_week = get_iso_week(resolved_date)

                if resolved_week in weekly_stats:
                    weekly_stats[resolved_week]["bugs_resolved"] += 1

                    points = bug.get("points") or 0
                    weekly_stats[resolved_week]["bugs_points_resolved"] += points

            except ValueError:
                continue

    cumulative_bugs = 0
    sorted_weeks = sorted(weekly_stats.keys())

    for week_key in sorted_weeks:
        stat = weekly_stats[week_key]

        stat["net_bugs"] = stat["bugs_created"] - stat["bugs_resolved"]
        stat["net_points"] = stat["bugs_points_created"] - stat["bugs_points_resolved"]

        cumulative_bugs += stat["net_bugs"]
        stat["cumulative_open_bugs"] = cumulative_bugs

    return [weekly_stats[week] for week in sorted_weeks]


def calculate_bug_metrics_summary(
    all_bug_issues: list[dict],
    timeline_filtered_bugs: list[dict],
    weekly_stats: list[dict],
    date_from=None,
    date_to=None,
    all_project_issues: list[dict] | None = None,
) -> dict:

    if not all_bug_issues and not timeline_filtered_bugs:
        return {
            "total_bugs": 0,
            "open_bugs": 0,
            "closed_bugs": 0,
            "resolution_rate": 0.0,
            "avg_resolution_time_days": 0.0,
            "bugs_created_last_4_weeks": 0,
            "bugs_resolved_last_4_weeks": 0,
            "trend_direction": "stable",
            "total_bug_points": 0,
            "open_bug_points": 0,
            "capacity_consumed_by_bugs": 0.0,
        }

    open_bugs = 0
    open_bug_points = 0
    open_bug_ages = []

    for issue in all_bug_issues:
        if "fields" in issue:
            fields = issue.get("fields", {})
            resolution_date = fields.get("resolutiondate")
            points = fields.get("customfield_10016") or 0
            created_str = fields.get("created", "")
        else:
            resolution_date = issue.get("resolved")
            points = issue.get("points") or 0
            created_str = issue.get("created", "")

        if not resolution_date:
            open_bugs += 1
            open_bug_points += points

            if created_str:
                try:
                    created = datetime.strptime(created_str[:19], "%Y-%m-%dT%H:%M:%S")
                    age_days = (datetime.now() - created).days
                    open_bug_ages.append(age_days)
                except ValueError:
                    pass

    avg_age_days = sum(open_bug_ages) / len(open_bug_ages) if open_bug_ages else 0

    import logging  # noqa: PLC0415

    logger = logging.getLogger(__name__)
    logger.info(
        f"[BUG CALC] Open bugs: count={open_bugs}, ages={len(open_bug_ages)}, "
        f"avg_age={avg_age_days:.1f}d"
    )

    total_bugs = len(timeline_filtered_bugs)
    closed_bugs = 0
    total_bug_points = 0
    resolution_times = []

    import logging  # noqa: PLC0415

    logger = logging.getLogger(__name__)
    logger.info(
        f"[BUG CALC] Calculating resolution from timeline_filtered_bugs: "
        f"count={total_bugs}, all_bugs={len(all_bug_issues)}"
    )

    for issue in timeline_filtered_bugs:
        if "fields" in issue:
            fields = issue.get("fields", {})
            resolution_date = fields.get("resolutiondate")
            points = fields.get("customfield_10016") or 0
            created_str = fields.get("created", "")
        else:
            resolution_date = issue.get("resolved")
            points = issue.get("points") or 0
            created_str = issue.get("created", "")

        total_bug_points += points

        if resolution_date:
            closed_bugs += 1

            if created_str:
                try:
                    created = datetime.strptime(created_str[:19], "%Y-%m-%dT%H:%M:%S")
                    resolved = datetime.strptime(
                        resolution_date[:19], "%Y-%m-%dT%H:%M:%S"
                    )
                    resolution_time = (resolved - created).days
                    resolution_times.append(resolution_time)
                except ValueError:
                    pass

    resolution_rate = closed_bugs / total_bugs if total_bugs > 0 else 0.0

    logger.info(
        f"[BUG CALC] Resolution rate: {closed_bugs}/{total_bugs} = "
        f"{resolution_rate:.4f} ({resolution_rate * 100:.2f}%)"
    )

    import logging  # noqa: PLC0415

    logger = logging.getLogger(__name__)
    logger.info(
        f"[BUG CALC] Resolution rate: closed={closed_bugs}, total={total_bugs}, "
        f"rate={resolution_rate * 100:.2f}%, all_bugs={len(all_bug_issues)}, "
        f"timeline_bugs={len(timeline_filtered_bugs)}"
    )

    avg_resolution_time_days = (
        sum(resolution_times) / len(resolution_times) if resolution_times else 0.0
    )

    bugs_created_last_4_weeks = 0
    bugs_resolved_last_4_weeks = 0

    if weekly_stats and len(weekly_stats) >= 4:
        recent_stats = weekly_stats[-4:]
        bugs_created_last_4_weeks = sum(
            week.get("bugs_created", 0) for week in recent_stats
        )
        bugs_resolved_last_4_weeks = sum(
            week.get("bugs_resolved", 0) for week in recent_stats
        )

    trend_direction = "stable"
    if bugs_created_last_4_weeks > 0 or bugs_resolved_last_4_weeks > 0:
        if bugs_resolved_last_4_weeks > bugs_created_last_4_weeks * 1.1:
            trend_direction = "improving"
        elif bugs_created_last_4_weeks > bugs_resolved_last_4_weeks * 1.1:
            trend_direction = "degrading"

    capacity_consumed_by_bugs = 0.0
    if all_project_issues:
        total_project_points = 0
        for issue in all_project_issues:
            if "fields" in issue:
                points = issue.get("fields", {}).get("customfield_10016") or 0
            else:
                points = issue.get("points") or 0
            total_project_points += points

        if total_project_points > 0:
            capacity_consumed_by_bugs = open_bug_points / total_project_points

    return {
        "total_bugs": total_bugs,
        "open_bugs": open_bugs,
        "closed_bugs": closed_bugs,
        "resolution_rate": resolution_rate,
        "avg_resolution_time_days": avg_resolution_time_days,
        "avg_age_days": avg_age_days,
        "bugs_created_last_4_weeks": bugs_created_last_4_weeks,
        "bugs_resolved_last_4_weeks": bugs_resolved_last_4_weeks,
        "trend_direction": trend_direction,
        "total_bug_points": total_bug_points,
        "open_bug_points": open_bug_points,
        "capacity_consumed_by_bugs": capacity_consumed_by_bugs,
        "date_from": date_from,
        "date_to": date_to,
    }


def forecast_bug_resolution(
    open_bugs: int, weekly_stats: list[dict], use_last_n_weeks: int = 8
) -> dict:

    if open_bugs == 0:
        return {
            "optimistic_weeks": 0,
            "most_likely_weeks": 0,
            "pessimistic_weeks": 0,
            "optimistic_date": calculate_future_date(0),
            "most_likely_date": calculate_future_date(0),
            "pessimistic_date": calculate_future_date(0),
            "avg_closure_rate": 0,
            "insufficient_data": False,
        }

    if len(weekly_stats) < 4:
        return {
            "optimistic_weeks": 0,
            "most_likely_weeks": 0,
            "pessimistic_weeks": 0,
            "optimistic_date": "",
            "most_likely_date": "",
            "pessimistic_date": "",
            "avg_closure_rate": 0,
            "insufficient_data": True,
        }

    recent_stats = weekly_stats[-use_last_n_weeks:]
    closure_rates = [week.get("bugs_resolved", 0) for week in recent_stats]

    analysis_start = recent_stats[0].get("week_start") if recent_stats else None
    analysis_end = recent_stats[-1].get("week_start") if recent_stats else None

    avg_closure_rate = sum(closure_rates) / len(closure_rates)

    if avg_closure_rate == 0:
        return {
            "optimistic_weeks": 0,
            "most_likely_weeks": 0,
            "pessimistic_weeks": 0,
            "optimistic_date": "",
            "most_likely_date": "",
            "pessimistic_date": "",
            "avg_closure_rate": 0,
            "insufficient_data": True,
        }

    std_dev = calculate_standard_deviation(closure_rates)

    optimistic_rate = avg_closure_rate + std_dev
    optimistic_rate = max(optimistic_rate, avg_closure_rate)

    pessimistic_rate = avg_closure_rate - std_dev
    pessimistic_rate = max(pessimistic_rate, 0.1)

    optimistic_weeks = int(open_bugs / optimistic_rate) + (
        1 if open_bugs % optimistic_rate > 0 else 0
    )
    most_likely_weeks = int(open_bugs / avg_closure_rate) + (
        1 if open_bugs % avg_closure_rate > 0 else 0
    )
    pessimistic_weeks = int(open_bugs / pessimistic_rate) + (
        1 if open_bugs % pessimistic_rate > 0 else 0
    )

    optimistic_weeks = min(optimistic_weeks, most_likely_weeks)
    pessimistic_weeks = max(pessimistic_weeks, most_likely_weeks)

    return {
        "optimistic_weeks": optimistic_weeks,
        "most_likely_weeks": most_likely_weeks,
        "pessimistic_weeks": pessimistic_weeks,
        "optimistic_date": calculate_future_date(optimistic_weeks),
        "most_likely_date": calculate_future_date(most_likely_weeks),
        "pessimistic_date": calculate_future_date(pessimistic_weeks),
        "avg_closure_rate": round(avg_closure_rate, 2),
        "insufficient_data": False,
        "analysis_start": analysis_start,
        "analysis_end": analysis_end,
        "weeks_analyzed": len(recent_stats),
    }


def get_iso_week(date: datetime) -> str:

    iso_calendar = date.isocalendar()
    return f"{iso_calendar[0]}-W{iso_calendar[1]:02d}"


def get_max_iso_week_for_year(year: int) -> int:

    last_day_of_year_week = datetime(year, 12, 28)
    return last_day_of_year_week.isocalendar()[1]


def get_week_start_date(iso_week: str) -> str:

    year, week = iso_week.split("-W")
    week_start = datetime.strptime(f"{year}-W{week}-1", "%G-W%V-%u")
    return week_start.date().isoformat()


def calculate_standard_deviation(values: list[float]) -> float:

    if not values or len(values) < 2:
        return 0.0

    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return variance**0.5


def calculate_future_date(weeks_ahead: int, base_date: datetime | None = None) -> str:

    if base_date is None:
        base_date = datetime.now()

    future_date = base_date + timedelta(weeks=weeks_ahead)
    return future_date.date().isoformat()


def generate_bug_weekly_forecast(
    weekly_stats: list[dict], use_last_n_weeks: int = 8
) -> dict:

    if not weekly_stats or len(weekly_stats) < 2:
        return {
            "created": {
                "most_likely": 0,
                "optimistic": 0,
                "pessimistic": 0,
                "next_week": "",
            },
            "resolved": {
                "most_likely": 0,
                "optimistic": 0,
                "pessimistic": 0,
                "next_week": "",
            },
            "insufficient_data": True,
        }

    recent_stats = (
        weekly_stats[-use_last_n_weeks:]
        if len(weekly_stats) > use_last_n_weeks
        else weekly_stats
    )

    bugs_created = [s["bugs_created"] for s in recent_stats]
    bugs_resolved = [s["bugs_resolved"] for s in recent_stats]

    avg_created = sum(bugs_created) / len(bugs_created)
    max_created = max(bugs_created) if bugs_created else 0
    min_created = min(bugs_created) if bugs_created else 0
    optimistic_created = max_created
    pessimistic_created = min_created
    most_likely_created = avg_created

    avg_resolved = sum(bugs_resolved) / len(bugs_resolved)
    max_resolved = max(bugs_resolved) if bugs_resolved else 0
    min_resolved = min(bugs_resolved) if bugs_resolved else 0
    optimistic_resolved = max_resolved
    pessimistic_resolved = min_resolved
    most_likely_resolved = avg_resolved

    last_week = recent_stats[-1]["week"]
    year, week_num = last_week.split("-W")

    last_week_date = dt.strptime(f"{year}-W{week_num}-1", "%Y-W%W-%w")
    next_week_date = last_week_date + timedelta(weeks=1)
    next_week_str = next_week_date.strftime("%Y-W%W")

    result = {
        "created": {
            "most_likely": round(most_likely_created, 1),
            "optimistic": round(optimistic_created, 1),
            "pessimistic": round(pessimistic_created, 1),
            "next_week": next_week_str,
        },
        "resolved": {
            "most_likely": round(most_likely_resolved, 1),
            "optimistic": round(optimistic_resolved, 1),
            "pessimistic": round(pessimistic_resolved, 1),
            "next_week": next_week_str,
        },
        "insufficient_data": False,
    }

    has_points = any(
        s.get("bugs_points_created", 0) > 0 or s.get("bugs_points_resolved", 0) > 0
        for s in recent_stats
    )
    if has_points:
        points_created = [s.get("bugs_points_created", 0) for s in recent_stats]
        points_resolved = [s.get("bugs_points_resolved", 0) for s in recent_stats]

        avg_points_created = sum(points_created) / len(points_created)
        max_points_created = max(points_created) if points_created else 0
        min_points_created = min(points_created) if points_created else 0

        avg_points_resolved = sum(points_resolved) / len(points_resolved)
        max_points_resolved = max(points_resolved) if points_resolved else 0
        min_points_resolved = min(points_resolved) if points_resolved else 0

        result["created_points"] = {
            "most_likely": round(avg_points_created, 1),
            "optimistic": round(max_points_created, 1),
            "pessimistic": round(min_points_created, 1),
            "next_week": next_week_str,
        }
        result["resolved_points"] = {
            "most_likely": round(avg_points_resolved, 1),
            "optimistic": round(max_points_resolved, 1),
            "pessimistic": round(min_points_resolved, 1),
            "next_week": next_week_str,
        }

    return result
