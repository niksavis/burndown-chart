import re
from datetime import datetime


def generate_query_name(jql: str, max_length: int = 50) -> str:

    if not jql or not jql.strip():
        return f"Custom Query {datetime.now().strftime('%Y-%m-%d')}"

    project = _extract_project(jql)
    issue_type = _extract_issue_type(jql)
    status = _extract_status(jql)
    priority = _extract_priority(jql)
    sprint = _extract_sprint(jql)
    time_range = _extract_time_range(jql)

    name_parts = []

    if project:
        name_parts.append(project)

    if issue_type and issue_type not in ["story", "task"]:
        if priority:
            name_parts.append(f"{priority} {issue_type}s")
        else:
            name_parts.append(f"{issue_type}s")
    elif priority:
        name_parts.append(f"{priority} Priority")

    if sprint:
        name_parts.append(sprint)
    elif status:
        name_parts.append(status)

    if time_range and not sprint:
        name_parts.append(time_range)

    if not name_parts:
        return f"Custom Query {datetime.now().strftime('%Y-%m-%d')}"

    if len(name_parts) == 1:
        component = name_parts[0]
        if project and component == project:
            name = f"{component} Project"
        else:
            name = component
    else:
        name = " - ".join(name_parts)

    if len(name) > max_length:
        name = name[: max_length - 3] + "..."

    return name


def _extract_project(jql: str) -> str | None:
    patterns = [
        r'project\s*=\s*(["\']?)([A-Z][A-Z0-9_-]*)\1',
        r'project\s+in\s*\(\s*(["\']?)([A-Z][A-Z0-9_-]*)\1',
    ]

    for pattern in patterns:
        match = re.search(pattern, jql, re.IGNORECASE)
        if match:
            return match.group(2).upper()

    return None


def _extract_issue_type(jql: str) -> str | None:
    patterns = [
        r'(?:type|issuetype)\s*=\s*(["\']?)(\w+)\1',
        r'(?:type|issuetype)\s+in\s*\(\s*(["\']?)(\w+)\1',
    ]

    for pattern in patterns:
        match = re.search(pattern, jql, re.IGNORECASE)
        if match:
            type_value = match.group(2).capitalize()
            return type_value

    return None


def _extract_status(jql: str) -> str | None:
    patterns = [
        r'status\s*=\s*(["\']?)(\w+(?:\s+\w+)?)\1',
        r'status\s+in\s*\(\s*(["\']?)(\w+(?:\s+\w+)?)\1',
    ]

    for pattern in patterns:
        match = re.search(pattern, jql, re.IGNORECASE)
        if match:
            status = match.group(2).replace("_", " ").title()
            return status

    return None


def _extract_priority(jql: str) -> str | None:
    patterns = [
        r'priority\s*=\s*(["\']?)(\w+)\1',
        r'priority\s+in\s*\(\s*(["\']?)(\w+)\1',
    ]

    for pattern in patterns:
        match = re.search(pattern, jql, re.IGNORECASE)
        if match:
            return match.group(2).capitalize()

    return None


def _extract_sprint(jql: str) -> str | None:
    jql_lower = jql.lower()

    if "opensprints()" in jql_lower:
        return "Open Sprints"
    if "closedsprints()" in jql_lower:
        return "Closed Sprints"
    if "futurespri nts()" in jql_lower:
        return "Future Sprints"

    match = re.search(r'sprint\s*=\s*(["\'])([^"\']+)\1', jql, re.IGNORECASE)
    if match:
        sprint_name = match.group(2)
        return sprint_name

    return None


def _extract_time_range(jql: str) -> str | None:
    patterns = [
        (r"created\s*>=\s*-(\d+)w", lambda m: f"Last {m.group(1)} Weeks"),
        (r"created\s*>=\s*-(\d+)d", lambda m: f"Last {m.group(1)} Days"),
        (r"created\s*>=\s*-(\d+)m", lambda m: f"Last {m.group(1)} Months"),
        (r"updated\s*>=\s*-(\d+)w", lambda m: f"Updated Last {m.group(1)} Weeks"),
        (r"updated\s*>=\s*-(\d+)d", lambda m: f"Updated Last {m.group(1)} Days"),
    ]

    for pattern, formatter in patterns:
        match = re.search(pattern, jql, re.IGNORECASE)
        if match:
            return formatter(match)

    if re.search(r'created\s*>=\s*["\']?\d{4}-\d{2}-\d{2}', jql, re.IGNORECASE):
        return "Since Date"

    return None


def validate_query_name(
    name: str, existing_names: list[str]
) -> tuple[bool, str | None]:

    if not name or not name.strip():
        return False, "Query name cannot be empty"

    name = name.strip()

    if len(name) < 3:
        return False, "Query name must be at least 3 characters"

    if len(name) > 100:
        return False, "Query name must be less than 100 characters"

    unsafe_chars = r'[<>:"/\\|?*]'
    if re.search(unsafe_chars, name):
        return False, 'Query name contains invalid characters (< > : " / \\ | ? *)'

    if any(existing.lower() == name.lower() for existing in existing_names):
        return False, f"Query '{name}' already exists. Choose a different name."

    return True, None
