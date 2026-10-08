import random
from datetime import datetime, timedelta


def generate_mock_bug_data(
    num_weeks: int = 12,
    bugs_per_week_range: tuple[int, int] = (5, 15),
    issue_types: list[str] | None = None,
    resolution_rate: float = 0.70,
    seed: int | None = None,
) -> list[dict]:

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

            created_date = week_date + timedelta(days=random.randint(0, 6))

            is_resolved = random.random() < resolution_rate
            resolution_date = None
            if is_resolved:
                days_to_resolve = random.randint(1, 21)
                resolution_date = created_date + timedelta(days=days_to_resolve)

            points_choices = [None, None, 1, 1, 2, 2, 3, 3, 5, 5, 8, 13]
            points = random.choice(points_choices)

            mock_issues.append(
                create_mock_bug(
                    key=f"MOCK-{len(mock_issues) + 1}",
                    issue_type=issue_type,
                    created_date=created_date,
                    resolved_date=resolution_date,
                    points=points,
                )
            )

    mock_issues.extend(generate_edge_case_bugs())

    return mock_issues


def generate_edge_case_bugs() -> list[dict]:

    now = datetime.now()
    edge_cases = []

    edge_cases.append(
        create_mock_bug(
            key="EDGE-1",
            issue_type="Bug",
            created_date=now - timedelta(days=30),
            resolved_date=now - timedelta(days=10),
            points=100,
        )
    )

    edge_cases.append(
        create_mock_bug(
            key="EDGE-2",
            issue_type="Defect",
            created_date=now - timedelta(weeks=20),
            resolved_date=now - timedelta(days=5),
            points=5,
        )
    )

    edge_cases.append(
        create_mock_bug(
            key="EDGE-3",
            issue_type="Bug",
            created_date=now - timedelta(days=14),
            resolved_date=None,
            points=None,
        )
    )

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

    if created_date is None:
        created_date = datetime.now()

    status = (
        "Done" if resolved_date else random.choice(["Open", "In Progress", "To Do"])
    )

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
            "customfield_10016": points,
        },
    }

    return issue
