import logging
from datetime import date, datetime

logger = logging.getLogger("burndown_chart")


def get_fixversions(issue: dict) -> list[dict]:

    try:
        if "fields" in issue and isinstance(issue.get("fields"), dict):
            return issue.get("fields", {}).get("fixVersions", [])
        else:
            return issue.get("fixVersions", [])
    except Exception as e:
        logger.error(
            f"Error getting fixVersions for issue {issue.get('key', 'UNKNOWN')}: {e}"
        )
        return []


def extract_fixversion_ids(issue: dict) -> set:

    try:
        fixversions = get_fixversions(issue)
        return {fv.get("id") for fv in fixversions if fv.get("id")}
    except Exception as e:
        logger.error(
            f"Error extracting fixVersion IDs for issue "
            f"{issue.get('key', 'UNKNOWN')}: {e}"
        )
        return set()


def extract_fixversion_names(issue: dict) -> set:

    try:
        fixversions = get_fixversions(issue)
        normalized_names = set()

        for fv in fixversions:
            name = fv.get("name")
            if name:
                normalized = name.lower().replace(" ", "_").replace("-", "_")
                normalized_names.add(normalized)

        return normalized_names
    except Exception as e:
        logger.error(
            f"Error extracting fixVersion names for issue "
            f"{issue.get('key', 'UNKNOWN')}: {e}"
        )
        return set()


def get_earliest_release_date(
    fixversions: list[dict], today: date | None = None
) -> date | None:

    if today is None:
        today = date.today()

    try:
        valid_dates = []
        for fv in fixversions:
            release_date_str = fv.get("releaseDate")
            if not release_date_str:
                continue

            try:
                release_date = datetime.strptime(release_date_str, "%Y-%m-%d").date()

                if release_date <= today:
                    valid_dates.append(release_date)
            except ValueError as e:
                logger.warning(f"Invalid releaseDate format: {release_date_str} - {e}")
                continue

        if not valid_dates:
            return None

        return min(valid_dates)

    except Exception as e:
        logger.error(f"Error getting earliest release date: {e}")
        return None


def get_fallback_release_date(issue: dict) -> date | None:

    try:
        resolution_date_str = issue.get("fields", {}).get("resolutiondate")
        if not resolution_date_str:
            return None

        resolution_datetime = datetime.fromisoformat(
            resolution_date_str.replace("Z", "+00:00")
        )
        return resolution_datetime.date()

    except Exception as e:
        logger.error(
            f"Error getting fallback release date for issue "
            f"{issue.get('key', 'UNKNOWN')}: {e}"
        )
        return None


def find_matching_operational_tasks(
    dev_issue: dict,
    operational_tasks: list[dict],
    match_by: str = "auto",
) -> list[tuple[dict, str]]:

    try:
        dev_fixversion_ids = extract_fixversion_ids(dev_issue)
        dev_fixversion_names = extract_fixversion_names(dev_issue)

        if not dev_fixversion_ids and not dev_fixversion_names:
            logger.debug(
                f"Development issue {dev_issue.get('key', 'UNKNOWN')} "
                f"has no fixVersions"
            )
            return []

        matching_tasks = []

        for op_task in operational_tasks:
            op_fixversion_ids = extract_fixversion_ids(op_task)
            op_fixversion_names = extract_fixversion_names(op_task)

            if match_by in ("id", "auto"):
                if dev_fixversion_ids & op_fixversion_ids:
                    matching_tasks.append((op_task, "id"))
                    logger.debug(
                        f"fixVersion ID match: {dev_issue.get('key')} "
                        f"<-> {op_task.get('key')} "
                        f"(IDs: {dev_fixversion_ids & op_fixversion_ids})"
                    )
                    continue

            if match_by in ("name", "auto"):
                if dev_fixversion_names & op_fixversion_names:
                    matching_tasks.append((op_task, "name"))
                    logger.debug(
                        f"fixVersion name match: {dev_issue.get('key')} "
                        f"<-> {op_task.get('key')} "
                        f"(Names: {dev_fixversion_names & op_fixversion_names})"
                    )
                    if match_by == "auto":
                        logger.warning(
                            f"fixVersion matched by name for "
                            f"{dev_issue.get('key')} <-> {op_task.get('key')} "
                            f"(consider verifying ID alignment)"
                        )

        return matching_tasks

    except Exception as e:
        logger.error(
            f"Error finding matching operational tasks for issue "
            f"{dev_issue.get('key', 'UNKNOWN')}: {e}"
        )
        return []


def get_deployment_date_from_operational_task(
    op_task: dict,
    matching_fixversion_ids: set | None = None,
    matching_fixversion_names: set | None = None,
) -> date | None:

    try:
        all_fixversions = get_fixversions(op_task)

        if matching_fixversion_ids or matching_fixversion_names:
            matching_fixversions = []
            for fv in all_fixversions:
                fv_id = fv.get("id")
                fv_name = fv.get("name")

                if matching_fixversion_ids and fv_id in matching_fixversion_ids:
                    matching_fixversions.append(fv)
                elif matching_fixversion_names and fv_name:
                    normalized_name = (
                        fv_name.lower().replace(" ", "_").replace("-", "_")
                    )
                    if normalized_name in matching_fixversion_names:
                        matching_fixversions.append(fv)
        else:
            matching_fixversions = all_fixversions

        if not matching_fixversions:
            logger.debug(
                f"Operational task {op_task.get('key', 'UNKNOWN')} "
                f"has no matching fixVersions"
            )
            return None

        earliest_date = get_earliest_release_date(matching_fixversions)

        if earliest_date:
            logger.debug(
                f"Operational task {op_task.get('key', 'UNKNOWN')}: "
                f"Earliest deployment date = {earliest_date}"
            )
            return earliest_date

        fallback_date = get_fallback_release_date(op_task)
        if fallback_date:
            logger.info(
                f"Operational task {op_task.get('key', 'UNKNOWN')}: "
                f"No releaseDate, using resolutiondate = {fallback_date}"
            )
            return fallback_date

        logger.warning(
            f"Operational task {op_task.get('key', 'UNKNOWN')}: "
            "No valid deployment date found "
            f"(no releaseDate or resolutiondate)"
        )
        return None

    except Exception as e:
        logger.error(
            f"Error getting deployment date from operational task "
            f"{op_task.get('key', 'UNKNOWN')}: {e}"
        )
        return None


def get_relevant_deployment_date(
    dev_issue: dict,
    operational_tasks: list[dict],
    deployment_ready_time: datetime | None = None,
) -> tuple[date, dict, str] | None:

    dev_key = dev_issue.get("key", "UNKNOWN")
    logger.info(
        f"[RELEVANT_DEPLOY] {dev_key}: Starting search, "
        f"ready_time={deployment_ready_time}"
    )

    try:
        matching_tasks = find_matching_operational_tasks(dev_issue, operational_tasks)
        logger.info(
            f"[RELEVANT_DEPLOY] {dev_key}: Found {len(matching_tasks)} "
            f"matching operational tasks"
        )

        if not matching_tasks:
            logger.debug(
                f"Development issue {dev_issue.get('key', 'UNKNOWN')}: "
                f"No matching operational tasks found"
            )
            return None

        deployment_dates = []
        for op_task, match_method in matching_tasks:
            dev_fixversion_ids = extract_fixversion_ids(dev_issue)
            dev_fixversion_names = extract_fixversion_names(dev_issue)

            logger.info(
                f"[RELEVANT_DEPLOY] {dev_key}: Getting deployment date from "
                f"{op_task.get('key')}, match_method={match_method}"
            )

            deployment_date = get_deployment_date_from_operational_task(
                op_task,
                matching_fixversion_ids=dev_fixversion_ids
                if match_method == "id"
                else None,
                matching_fixversion_names=dev_fixversion_names
                if match_method == "name"
                else None,
            )

            logger.info(
                f"[RELEVANT_DEPLOY] {dev_key}: Deployment date from "
                f"{op_task.get('key')} = {deployment_date}"
            )

            if deployment_date:
                deployment_dates.append((deployment_date, op_task, match_method))

        if not deployment_dates:
            logger.warning(
                f"[RELEVANT_DEPLOY] {dev_key}: [X] Found {len(matching_tasks)} "
                f"matching operational tasks, but NONE have valid deployment dates!"
            )
            return None

        if deployment_ready_time:
            ready_date = deployment_ready_time.date()
            logger.info(
                f"[RELEVANT_DEPLOY] {dev_key}: Ready date = {ready_date}, "
                f"checking {len(deployment_dates)} deployment dates"
            )

            for dep_date, op_task, _method in deployment_dates:
                logger.info(
                    f"[RELEVANT_DEPLOY] {dev_key}:   - {op_task.get('key')}: "
                    f"deployment={dep_date}, after_ready={dep_date >= ready_date}"
                )

            after_ready = [d for d in deployment_dates if d[0] >= ready_date]
            logger.info(
                f"[RELEVANT_DEPLOY] {dev_key}: {len(after_ready)} deployments "
                f"after ready time"
            )

            if after_ready:
                relevant = min(after_ready, key=lambda x: x[0])
                logger.warning(
                    f"[RELEVANT_DEPLOY] {dev_key}: [OK] USING deployment = "
                    f"{relevant[0]} from {relevant[1].get('key')} "
                    f"(after ready time {ready_date}, matched by {relevant[2]})"
                )
                return relevant
            else:
                logger.warning(
                    f"[RELEVANT_DEPLOY] {dev_key}: [X] All {len(deployment_dates)} "
                    f"deployments are BEFORE ready time {ready_date}. "
                    f"Using earliest anyway."
                )

        earliest = min(deployment_dates, key=lambda x: x[0])
        logger.debug(
            f"Development issue {dev_issue.get('key', 'UNKNOWN')}: "
            f"Earliest deployment = {earliest[0]} from {earliest[1].get('key')} "
            f"(matched by {earliest[2]})"
        )

        return earliest

    except Exception as e:
        logger.error(
            f"Error getting relevant deployment date for issue "
            f"{dev_issue.get('key', 'UNKNOWN')}: {e}"
        )
        return None


def get_earliest_deployment_date(
    dev_issue: dict,
    operational_tasks: list[dict],
) -> tuple[date, dict, str] | None:

    try:
        matching_tasks = find_matching_operational_tasks(dev_issue, operational_tasks)

        if not matching_tasks:
            logger.debug(
                f"Development issue {dev_issue.get('key', 'UNKNOWN')}: "
                f"No matching operational tasks found"
            )
            return None

        deployment_dates = []
        for op_task, match_method in matching_tasks:
            dev_fixversion_ids = extract_fixversion_ids(dev_issue)
            dev_fixversion_names = extract_fixversion_names(dev_issue)

            deployment_date = get_deployment_date_from_operational_task(
                op_task,
                matching_fixversion_ids=dev_fixversion_ids
                if match_method == "id"
                else None,
                matching_fixversion_names=dev_fixversion_names
                if match_method == "name"
                else None,
            )

            if deployment_date:
                deployment_dates.append((deployment_date, op_task, match_method))

        if not deployment_dates:
            logger.debug(
                f"Development issue {dev_issue.get('key', 'UNKNOWN')}: "
                f"Found {len(matching_tasks)} matching operational tasks, "
                f"but none have valid deployment dates"
            )
            return None

        earliest = min(deployment_dates, key=lambda x: x[0])
        logger.debug(
            f"Development issue {dev_issue.get('key', 'UNKNOWN')}: "
            f"Earliest deployment = {earliest[0]} from {earliest[1].get('key')} "
            f"(matched by {earliest[2]})"
        )

        return earliest

    except Exception as e:
        logger.error(
            f"Error getting earliest deployment date for issue "
            f"{dev_issue.get('key', 'UNKNOWN')}: {e}"
        )
        return None


def filter_operational_tasks_by_fixversion(
    operational_tasks: list[dict],
    dev_fixversion_ids: set,
    dev_fixversion_names: set,
) -> list[dict]:

    try:
        filtered_tasks = []

        for op_task in operational_tasks:
            op_fixversion_ids = extract_fixversion_ids(op_task)
            op_fixversion_names = extract_fixversion_names(op_task)

            if (dev_fixversion_ids & op_fixversion_ids) or (
                dev_fixversion_names & op_fixversion_names
            ):
                filtered_tasks.append(op_task)

        logger.info(
            f"Filtered operational tasks: {len(filtered_tasks)} "
            f"of {len(operational_tasks)} "
            f"match development issue fixVersions"
        )

        return filtered_tasks

    except Exception as e:
        logger.error(f"Error filtering operational tasks by fixVersion: {e}")
        return operational_tasks


def build_fixversion_release_map(
    operational_tasks: list[dict],
    valid_fix_versions: set | None = None,
    flow_end_statuses: list[str] | None = None,
) -> dict[str, datetime]:

    release_map: dict[str, datetime] = {}

    for issue in operational_tasks:
        if flow_end_statuses:
            if "fields" in issue and isinstance(issue.get("fields"), dict):
                status = issue.get("fields", {}).get("status", {}).get("name", "")
            else:
                status = issue.get("status", "")

            if status not in flow_end_statuses:
                continue

        if "fields" in issue and isinstance(issue.get("fields"), dict):
            fix_versions = issue.get("fields", {}).get("fixVersions") or []
        else:
            fix_versions = issue.get("fixVersions") or []
        for fv in fix_versions:
            fv_name = fv.get("name")
            release_date_str = fv.get("releaseDate")

            if not fv_name or not release_date_str:
                continue

            if valid_fix_versions and fv_name not in valid_fix_versions:
                continue

            try:
                release_date = datetime.fromisoformat(release_date_str)
                if fv_name not in release_map or release_date < release_map[fv_name]:
                    release_map[fv_name] = release_date
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid releaseDate for fixVersion {fv_name}: {e}")
                continue

    logger.info(
        f"Built fixVersion release map: {len(release_map)} versions with release dates"
    )
    if release_map:
        sample = list(release_map.items())[:3]
        logger.debug(f"Sample: {sample}")

    return release_map


def get_deployment_date_for_issue(
    issue: dict,
    fixversion_release_map: dict[str, datetime],
) -> datetime | None:

    if "fields" in issue and isinstance(issue.get("fields"), dict):
        fix_versions = issue.get("fields", {}).get("fixVersions") or []
    else:
        fix_versions = issue.get("fixVersions") or []

    deployment_dates = []
    for fv in fix_versions:
        fv_name = fv.get("name")
        if fv_name and fv_name in fixversion_release_map:
            deployment_dates.append(fixversion_release_map[fv_name])

    if not deployment_dates:
        return None

    return min(deployment_dates)


def filter_issues_deployed_in_week(
    issues: list[dict],
    fixversion_release_map: dict[str, datetime],
    week_start: datetime,
    week_end: datetime,
) -> list[dict]:

    filtered = []
    for issue in issues:
        deployment_date = get_deployment_date_for_issue(issue, fixversion_release_map)
        if deployment_date and week_start <= deployment_date < week_end:
            filtered.append(issue)

    logger.debug(
        f"Filtered {len(filtered)} of {len(issues)} issues deployed in week "
        f"{week_start.date()} to {week_end.date()}"
    )
    return filtered
