"""Mock bug data generator for testing.

Provides realistic bug distributions for unit and integration tests without
requiring external JIRA API access.
"""

import random
from datetime import datetime, timedelta


def generate_mock_bug_data(
    num_weeks: int = 12,
    bugs_per_week_range: tuple[int, int] = (5, 15),
    issue_types: list[str] | None = None,
    resolution_rate: float = 0.70,
    seed: int | None = None,
) -> list[dict]:
    """Generate realistic mock bug data for testing.

    Args:
        num_weeks: Number of weeks of historical data to generate
        bugs_per_week_range: (min, max) bugs created per week
        issue_types: List of issue type names (defaults to ["Bug", "Defect", "Incident"])
        resolution_rate: Percentage of bugs that get resolved (0.0-1.0)
        seed: Random seed for reproducibility

    Returns:
        List of mock JIRA issue dictionaries with bug characteristics

    Example:
        >>> bugs = generate_mock_bug_data(num_weeks=4, bugs_per_week_range=(10, 20), seed=42)
        >>> len(bugs) >= 40  # At least 40 bugs for 4 weeks
        True
        >>> all("issuetype" in bug["fields"] for bug in bugs)
        True
    """
    if seed is not None:
        random.seed(seed)

    if issue_types is None:
        issue_types = ["Bug", "Defect", "Incident"]

    mock_issues = []
    base_date = datetime.now() - timedelta(weeks=num_weeks)

    for week in range(num_weeks):
        week_date = base_date + timedelta(weeks=week)
        num_bugs = random.randint(*bugs_per_week_range)

        for _ in range(num_bugs):
            issue_type = random.choice(issue_types)

            # Realistic lifecycle - bugs created within the week
            created_date = week_date + timedelta(days=random.randint(0, 6))

            # Resolution based on resolution_rate
            is_resolved = random.random() < resolution_rate
            resolution_date = None
            if is_resolved:
                # Bugs typically resolve within 1-21 days
                days_to_resolve = random.randint(1, 21)
                resolution_date = created_date + timedelta(days=days_to_resolve)

            # Story points distribution (some bugs have none, others 1-13)
            points_choices = [None, None, 1, 1, 2, 2, 3, 3, 5, 5, 8, 13]
            points = random.choice(points_choices)

            # Create mock JIRA issue
            mock_issues.append(
                create_mock_bug(
                    key=f"MOCK-{len(mock_issues) + 1}",
                    issue_type=issue_type,
                    created_date=created_date,
                    resolved_date=resolution_date,
                    points=points,
                )
            )

    # Add edge cases
    mock_issues.extend(generate_edge_case_bugs())

    return mock_issues


def generate_edge_case_bugs() -> list[dict]:
    """Generate edge case bug scenarios for boundary testing.

    Returns:
        List of edge case bug issues

    Edge cases included:
        - Bug with outlier story points (100+)
        - Bug created before timeline but closed within
        - Bug with no story points
        - Bug with zero resolution time (same day)
        - Bug with very long resolution time
    """
    now = datetime.now()
    edge_cases = []

    # Edge case 1: Bug with outlier story points (100)
    edge_cases.append(
        create_mock_bug(
            key="EDGE-1",
            issue_type="Bug",
            created_date=now - timedelta(days=30),
            resolved_date=now - timedelta(days=10),
            points=100,
        )
    )

    # Edge case 2: Bug created before timeline but closed recently
    edge_cases.append(
        create_mock_bug(
            key="EDGE-2",
            issue_type="Defect",
            created_date=now - timedelta(weeks=20),
            resolved_date=now - timedelta(days=5),
            points=5,
        )
    )

    # Edge case 3: Bug with no story points
    edge_cases.append(
        create_mock_bug(
            key="EDGE-3",
            issue_type="Bug",
            created_date=now - timedelta(days=14),
            resolved_date=None,
            points=None,
        )
    )

    # Edge case 4: Bug with zero resolution time (same day)
    same_day = now - timedelta(days=7)
    edge_cases.append(
        create_mock_bug(
            key="EDGE-4",
            issue_type="Incident",
            created_date=same_day,
            resolved_date=same_day + timedelta(hours=2),
            points=1,
        )
    )

    # Edge case 5: Bug with very long resolution time (60 days)
    edge_cases.append(
        create_mock_bug(
            key="EDGE-5",
            issue_type="Bug",
            created_date=now - timedelta(days=90),
            resolved_date=now - timedelta(days=30),
            points=13,
        )
    )

    return edge_cases


def create_mock_bug(
    key: str,
    issue_type: str = "Bug",
    created_date: datetime | None = None,
    resolved_date: datetime | None = None,
    points: int | None = None,
) -> dict:
    """Create a single mock bug issue.

    Args:
        key: JIRA issue key (e.g., "MOCK-123")
        issue_type: Issue type name
        created_date: Creation datetime (defaults to now)
        resolved_date: Resolution datetime (None = still open)
        points: Story points (None = no points)

    Returns:
        Mock JIRA issue dictionary matching JIRA API structure
    """
    if created_date is None:
        created_date = datetime.now()

    # Determine status based on resolution
    status = (
        "Done" if resolved_date else random.choice(["Open", "In Progress", "To Do"])
    )

    # Build JIRA-like issue structure
    issue = {
        "key": key,
        "fields": {
            "issuetype": {"name": issue_type},
            "created": created_date.strftime("%Y-%m-%dT%H:%M:%S.000+0000"),
            "resolutiondate": (
                resolved_date.strftime("%Y-%m-%dT%H:%M:%S.000+0000")
                if resolved_date
                else None
            ),
            "status": {"name": status},
            "customfield_10016": points,  # Story points field
        },
    }

    return issue
