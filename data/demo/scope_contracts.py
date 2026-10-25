from data.demo.contract_types import make_contracts

SCOPE_CONTRACTS = make_contracts(
    "scope-zero-baseline",
    "data.scope_metrics.calculate_scope_change_rate",
    "tab-scope-tracking",
    (
        ("zero-baseline-item-growth", "growth.items_rate", None),
        ("zero-baseline-point-growth", "growth.points_rate", None),
        ("creation-delivery-item-ratio", "growth.throughput_ratio.items", 1.5),
        ("creation-delivery-point-ratio", "growth.throughput_ratio.points", 1.5),
    ),
    backlog="burndownchart-imp031",
    derivation="Initial scope0 makes percent growth undefined. 48/32 and96/64 give ratio1.5.",
)
SCOPE_CONTRACTS += make_contracts(
    "scope-zero-baseline",
    "data.scope_metrics.calculate_scope_stability_index",
    "tab-scope-tracking",
    (
        ("zero-initial-items-stability", "stability.items_stability", 0),
        ("zero-initial-points-stability", "stability.points_stability", 0),
    ),
    backlog="burndownchart-imp031",
    derivation="Original scope0 of current48items/96points gives original-scope share0",
)
SCOPE_CONTRACTS += make_contracts(
    "scope-positive-window",
    "data.scope_metrics.calculate_scope_change_rate",
    "tab-scope-tracking",
    (
        ("positive-item-growth", "growth.items_rate", 300),
        ("positive-point-growth", "growth.points_rate", 300),
        ("positive-item-stability", "stability.items_stability", 0.25),
        ("positive-point-stability", "stability.points_stability", 0.25),
    ),
    selection="Last4weeks carry8items/16points; create24/48 and complete16/32",
    derivation="Created/original=24/8=48/16=300%; original/total=8/32=16/64=0.25",
)
SCOPE_CONTRACTS += make_contracts(
    "scope-threshold-calibration",
    "data.scope_metrics.check_scope_change_threshold",
    "tab-scope-tracking",
    (("scope-threshold-warning", "threshold.status", "warning"),),
    selection="Calibration baseline48items/96points, threshold25%; recorded creations48/96",
    derivation="100percent growth exceeds25percent and creation/delivery1.5 exceeds1",
)
for week in ("2025-W50", "2026-W01", "2026-W05"):
    SCOPE_CONTRACTS += make_contracts(
        "scope-weekly-growth",
        "data.scope_metrics.calculate_weekly_scope_growth",
        "tab-scope-tracking",
        (
            (f"weekly-net-items-{week}", f"{week}.items_growth", 2),
            (f"weekly-net-points-{week}", f"{week}.points_growth", 4),
        ),
        backlog="burndownchart-0tv1mh",
        derivation="Each week creates6/12 and completes4/8, for net2items/4points; ISO-year keys",
    )
