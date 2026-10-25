from data.demo.contract_types import make_contracts

WORK_CONTRACTS = make_contracts(
    "active-work",
    "data.active_work_manager.get_active_work_data",
    "tab-active-work-timeline",
    (
        ("epic-items", "DEMO-100.total_issues", 46),
        ("epic-completed", "DEMO-100.completed_issues", 31),
        ("epic-wip", "DEMO-100.in_progress_issues", 10),
        ("epic-todo", "DEMO-100.todo_issues", 5),
        ("epic-points", "DEMO-100.total_points", 92),
        ("epic-completed-points", "DEMO-100.completed_points", 61.5),
        ("epic-completion", "DEMO-100.completion_pct", 66.8),
        ("unparented-items", "No Parent.total_issues", 2),
    ),
    derivation="Exclude17(open1.5points) and34(done2.5points):46/92total;31/61.5done;10WIP",
)
WORK_CONTRACTS += make_contracts(
    "active-completed",
    "data.active_work_completed.get_completed_items_by_week",
    "tab-active-work-timeline",
    (
        ("recent-completed-items", "2026-W05.total_issues", 4),
        ("recent-completed-points", "2026-W05.total_points", 8),
        ("previous-completed-items", "2026-W04.total_issues", 4),
        ("previous-completed-points", "2026-W04.total_points", 8),
    ),
    selection="Current ISO week5 and previous week4",
    derivation="Each selected week completes one Story/Bug/Task/Risk, totaling4items and8points",
)
WORK_CONTRACTS += make_contracts(
    "sprint-progress",
    "data.sprint_manager.calculate_sprint_progress",
    "tab-sprint-tracker",
    (
        ("sprint-items", "Demo Sprint 4.total_issues", 10),
        ("sprint-completed", "Demo Sprint 4.completed_issues", 6),
        ("sprint-wip", "Demo Sprint 4.wip_issues", 4),
        ("sprint-todo", "Demo Sprint 4.todo_issues", 0),
        ("sprint-points", "Demo Sprint 4.total_points", 21),
        ("sprint-completed-points", "Demo Sprint 4.completed_points", 13),
        ("sprint-completion", "Demo Sprint 4.completion_percentage", 60),
        (
            "sprint-points-completion",
            "Demo Sprint 4.points_completion_percentage",
            61.9,
        ),
    ),
    selection="Active Sprint4; Story/Bug/Task types; Risk excluded as in actual tracker",
    derivation="Ten tracked items;6done;24scope points minus3Risk=21;16done minus3=13",
)
WORK_CONTRACTS += make_contracts(
    "sprint-progress",
    "data.sprint_manager.calculate_sprint_progress",
    "tab-sprint-tracker",
    (
        ("reopened-sprint-items", "Demo Sprint 1.total_issues", 8),
        ("reopened-sprint-completed", "Demo Sprint 1.completed_issues", 3),
        ("reopened-sprint-points", "Demo Sprint 1.total_points", 15),
        ("reopened-sprint-done-points", "Demo Sprint 1.completed_points", 5.5),
        ("moved-sprint-items", "Demo Sprint 2.total_issues", 11),
    ),
    scenario="reopened",
    selection="Sprint1 moves Bug2 toSprint2; removesTask3; reopensStory1",
    derivation="10-2=8members;6-2moved/removed-1reopen=3done;21-2.5-3.5=15points;13-7.5=5.5done",
)
WORK_CONTRACTS += make_contracts(
    "sprint-daily",
    "data.sprint_snapshot_calculator.calculate_daily_sprint_snapshots",
    "tab-sprint-tracker",
    (
        ("sprint-recorded-items", "Demo Sprint 4.dates.2026-01-29.total_count", 10),
        (
            "sprint-recorded-completed",
            "Demo Sprint 4.dates.2026-01-29.completed_count",
            6,
        ),
        ("sprint-recorded-points", "Demo Sprint 4.dates.2026-01-29.total_scope", 21),
        (
            "sprint-recorded-done-points",
            "Demo Sprint 4.dates.2026-01-29.completed_points",
            13,
        ),
        ("sprint-future-actuals", "Demo Sprint 4.future_observations", 0),
    ),
    backlog="burndownchart-imp048",
    selection="Active Sprint4 daily records at January29 evaluation date",
    derivation="Both weeks created beforeJan29;6done/13points; future actuals unavailable",
)
