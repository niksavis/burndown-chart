from data.demo.contract_types import make_contracts

WEEKLY_CONTRACTS = ()
for index, week in enumerate(
    (
        "2025-W50",
        "2025-W51",
        "2025-W52",
        "2026-W01",
        "2026-W02",
        "2026-W03",
        "2026-W04",
        "2026-W05",
    ),
    start=1,
):
    WEEKLY_CONTRACTS += make_contracts(
        "statistics-weekly",
        "data.jira.data_transformer.jira_to_csv_format",
        "tab-statistics-data",
        (
            (f"recorded-items-{week}", f"{week}.completed_items", 4),
            (f"recorded-points-{week}", f"{week}.completed_points", 8),
            (f"created-items-{week}", f"{week}.created_items", 6),
            (f"created-points-{week}", f"{week}.created_points", 12),
            (f"remaining-items-{week}", f"{week}.remaining_items", 2 * index),
            (f"remaining-points-{week}", f"{week}.remaining_total_points", 4 * index),
        ),
        selection=f"Recorded ISO week {week}",
        derivation="Each week adds6items/12points, completes4/8. Backlog rises2items/4points.",
    )
