"""
Smart Query Name Generator

Generates human-readable names from JQL queries for better query organization.
Extracts key components (project, status, type, time range) and formats them
into concise, descriptive names.

Examples:
    "project = KAFKA" → "KAFKA Project"
    "project = KAFKA AND status = Done" → "KAFKA - Done"
    "sprint in openSprints()" → "Open Sprints"
    "type = Bug AND priority = High" → "High Priority Bugs"
    "created >= -12w" → "Last 12 Weeks"

For complex queries, falls back to timestamped generic name.
"""

import re
from datetime import datetime
from typing import Optional


def generate_query_name(jql: str, max_length: int = 50) -> str:
    """
    Generate human-readable name from JQL query string.

    Analyzes JQL to extract meaningful components and formats them into
    a concise, descriptive name. Prioritizes the most significant query
    aspects in this order:
    1. Project name
    2. Issue type
    3. Status/Sprint
    4. Priority
    5. Time range

    Args:
        jql: JQL query string
        max_length: Maximum length for generated name (default: 50)

    Returns:
        Human-readable query name, truncated to max_length if needed

    Examples:
        >>> generate_query_name("project = KAFKA")
        "KAFKA Project"
        >>> generate_query_name("project = KAFKA AND status = Done")
        "KAFKA - Done"
        >>> generate_query_name("type = Bug AND priority = High")
        "High Priority Bugs"
    """
    if not jql or not jql.strip():
        return f"Custom Query {datetime.now().strftime('%Y-%m-%d')}"

    # Extract components
    project = _extract_project(jql)
    issue_type = _extract_issue_type(jql)
    status = _extract_status(jql)
    priority = _extract_priority(jql)
    sprint = _extract_sprint(jql)
    time_range = _extract_time_range(jql)

    # Build name from components
    name_parts = []

    # Start with project if exists
    if project:
        name_parts.append(project)

    # Add issue type if significant
    if issue_type and issue_type not in ["story", "task"]:  # Skip generic types
        if priority:
            name_parts.append(f"{priority} {issue_type}s")
        else:
            name_parts.append(f"{issue_type}s")
    elif priority:
        name_parts.append(f"{priority} Priority")

    # Add status or sprint
    if sprint:
        name_parts.append(sprint)
    elif status:
        name_parts.append(status)

    # Add time range if no other temporal info
    if time_range and not sprint:
        name_parts.append(time_range)

    # Construct final name
    if not name_parts:
        # Fallback for complex/unrecognized queries
        return f"Custom Query {datetime.now().strftime('%Y-%m-%d')}"

    if len(name_parts) == 1:
        # Single component - add context
        component = name_parts[0]
        if project and component == project:
            name = f"{component} Project"
        else:
            name = component
    else:
        # Multiple components - join with separator
        name = " - ".join(name_parts)

    # Truncate if needed
    if len(name) > max_length:
        name = name[: max_length - 3] + "..."

    return name


def _extract_project(jql: str) -> Optional[str]:
    """Extract project name from JQL."""
    # Match: project = KAFKA, project in (KAFKA, TEST), project = "KAFKA"
    patterns = [
        r'project\s*=\s*(["\']?)([A-Z][A-Z0-9_-]*)\1',
        r'project\s+in\s*\(\s*(["\']?)([A-Z][A-Z0-9_-]*)\1',
    ]

    for pattern in patterns:
        match = re.search(pattern, jql, re.IGNORECASE)
        if match:
            return match.group(2).upper()

    return None


def _extract_issue_type(jql: str) -> Optional[str]:
    """Extract issue type from JQL."""
    # Match: type = Bug, issuetype = Story, type in (Bug, Epic)
    patterns = [
        r'(?:type|issuetype)\s*=\s*(["\']?)(\w+)\1',
        r'(?:type|issuetype)\s+in\s*\(\s*(["\']?)(\w+)\1',
    ]

    for pattern in patterns:
        match = re.search(pattern, jql, re.IGNORECASE)
        if match:
            # Extract the type value (it's in group 2 for both patterns)
            type_value = match.group(2).capitalize()
            return type_value

    return None


def _extract_status(jql: str) -> Optional[str]:
    """Extract status from JQL."""
    # Match: status = Done, status in (Done, Closed)
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


def _extract_priority(jql: str) -> Optional[str]:
    """Extract priority from JQL."""
    # Match: priority = High, priority in (High, Critical)
    patterns = [
        r'priority\s*=\s*(["\']?)(\w+)\1',
        r'priority\s+in\s*\(\s*(["\']?)(\w+)\1',
    ]

    for pattern in patterns:
        match = re.search(pattern, jql, re.IGNORECASE)
        if match:
            return match.group(2).capitalize()

    return None


def _extract_sprint(jql: str) -> Optional[str]:
    """Extract sprint information from JQL."""
    jql_lower = jql.lower()

    # Check for sprint functions
    if "opensprints()" in jql_lower:
        return "Open Sprints"
    if "closedsprints()" in jql_lower:
        return "Closed Sprints"
    if "futurespri nts()" in jql_lower:
        return "Future Sprints"

    # Match: sprint = "Sprint 23"
    match = re.search(r'sprint\s*=\s*(["\'])([^"\']+)\1', jql, re.IGNORECASE)
    if match:
        sprint_name = match.group(2)
        # Simplify "Sprint 23" to "Sprint 23"
        return sprint_name

    return None


def _extract_time_range(jql: str) -> Optional[str]:
    """Extract time range from JQL."""
    # Match patterns like: created >= -12w, updated >= -30d
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

    # Match: created >= "2024-01-01"
    if re.search(r'created\s*>=\s*["\']?\d{4}-\d{2}-\d{2}', jql, re.IGNORECASE):
        return "Since Date"

    return None


def validate_query_name(
    name: str, existing_names: list[str]
) -> tuple[bool, Optional[str]]:
    """
    Validate query name for uniqueness and format.

    Args:
        name: Proposed query name
        existing_names: List of existing query names in profile

    Returns:
        Tuple of (is_valid, error_message)
        If valid: (True, None)
        If invalid: (False, "Error message")

    Examples:
        >>> validate_query_name("My Query", ["Other Query"])
        (True, None)
        >>> validate_query_name("My Query", ["My Query"])
        (False, "Query 'My Query' already exists")
    """
    if not name or not name.strip():
        return False, "Query name cannot be empty"

    name = name.strip()

    if len(name) < 3:
        return False, "Query name must be at least 3 characters"

    if len(name) > 100:
        return False, "Query name must be less than 100 characters"

    # Check for unsafe characters (filesystem)
    unsafe_chars = r'[<>:"/\\|?*]'
    if re.search(unsafe_chars, name):
        return False, 'Query name contains invalid characters (< > : " / \\ | ? *)'

    # Check for uniqueness (case-insensitive)
    if any(existing.lower() == name.lower() for existing in existing_names):
        return False, f"Query '{name}' already exists. Choose a different name."

    return True, None
