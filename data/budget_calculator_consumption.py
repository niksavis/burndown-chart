import logging
from pathlib import Path

from data.budget_calculator_core import _get_current_budget, _get_velocity
from data.database import get_db_connection
from data.iso_week_bucketing import get_last_n_weeks
from data.metrics_snapshots import get_metric_snapshot, load_snapshots

logger = logging.getLogger(__name__)


def calculate_budget_consumed(
    profile_id: str, query_id: str, week_label: str, db_path: Path | None = None
) -> tuple[float, float, float]:

    try:
        conn_context = (
            get_db_connection() if db_path is None else get_db_connection(db_path)
        )
        with conn_context as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT time_allocated_weeks, team_cost_per_week_eur,
                       budget_total_eur, currency_symbol
                FROM budget_settings
                WHERE profile_id = ? AND query_id = ?
            """,
                (profile_id, query_id),
            )

            result = cursor.fetchone()
            if not result:
                return 0.0, 0.0, 0.0

            budget = {
                "time_allocated_weeks": result[0] or 0,
                "team_cost_per_week_eur": result[1] or 0.0,
                "budget_total_eur": result[2] or 0.0,
                "currency_symbol": result[3] or "€",
            }

            cursor.execute(
                """
                SELECT SUM(completed_items)
                FROM project_statistics
                WHERE profile_id = ?
                  AND query_id = ?
                  AND week_label <= ?
            """,
                (profile_id, query_id, week_label),
            )

            result = cursor.fetchone()
            completed_items = result[0] if result and result[0] else 0

        velocity = _get_velocity(profile_id, query_id, week_label, 4, db_path)
        if velocity > 0:
            cost_per_item = budget["team_cost_per_week_eur"] / velocity
            consumed_eur = completed_items * cost_per_item
        else:
            consumed_eur = 0.0

        budget_total = budget["budget_total_eur"]
        percentage = (consumed_eur / budget_total * 100) if budget_total > 0 else 0.0

        return consumed_eur, budget_total, percentage

    except Exception as e:
        logger.error(f"Failed to calculate budget consumed: {e}")
        return 0.0, 0.0, 0.0


def calculate_cost_breakdown_by_type(
    profile_id: str, query_id: str, week_label: str, db_path: Path | None = None
) -> dict[str, dict[str, float]]:

    try:
        budget = _get_current_budget(profile_id, query_id, db_path)
        if not budget:
            logger.info("[COST BREAKDOWN] No budget configured")
            return _empty_breakdown()

        velocity = _get_velocity(profile_id, query_id, week_label, 4, db_path)
        if velocity <= 0:
            logger.info("[COST BREAKDOWN] Velocity is zero")
            return _empty_breakdown()

        cost_per_item = budget["team_cost_per_week_eur"] / velocity
        logger.info(f"[COST BREAKDOWN] Cost per item: €{cost_per_item:.2f}")

        snapshots = load_snapshots()
        if not snapshots:
            logger.info("[COST BREAKDOWN] No metric snapshots found")
            return _empty_breakdown()

        flow_counts = {"Feature": 0, "Defect": 0, "Technical Debt": 0, "Risk": 0}

        for _week, metrics in snapshots.items():
            velocity_data = metrics.get("flow_velocity", {})
            distribution = velocity_data.get("distribution", {})

            if distribution:
                flow_counts["Feature"] += distribution.get("feature", 0)
                flow_counts["Defect"] += distribution.get("defect", 0)
                flow_counts["Technical Debt"] += distribution.get("tech_debt", 0)
                flow_counts["Risk"] += distribution.get("risk", 0)

        total_items = sum(flow_counts.values())
        logger.info(
            f"[COST BREAKDOWN] Total items across all weeks: {total_items} "
            f"(Feature={flow_counts['Feature']}, Defect={flow_counts['Defect']}, "
            f"Tech Debt={flow_counts['Technical Debt']}, Risk={flow_counts['Risk']})"
        )

        if total_items == 0:
            logger.info("[COST BREAKDOWN] No completed items found in snapshots")
            return _empty_breakdown()

        breakdown = {}
        for flow_type, count in flow_counts.items():
            cost = count * cost_per_item
            percentage = (count / total_items * 100) if total_items > 0 else 0.0
            breakdown[flow_type] = {
                "cost": cost,
                "count": count,
                "percentage": percentage,
            }
            logger.info(
                f"[COST BREAKDOWN] {flow_type}: {count} items, "
                f"€{cost:.2f} ({percentage:.1f}%)"
            )

        return breakdown

    except Exception as e:
        logger.error(f"Failed to calculate cost breakdown: {e}", exc_info=True)
        return _empty_breakdown()


def calculate_runway(
    profile_id: str,
    query_id: str,
    week_label: str,
    data_points_count: int = 4,
    db_path: Path | None = None,
) -> tuple[float, float]:

    try:
        budget = _get_current_budget(profile_id, query_id, db_path)
        if not budget or budget["budget_total_eur"] <= 0:
            return 0.0, 0.0

        consumed, total, _ = calculate_budget_consumed(
            profile_id, query_id, week_label, db_path
        )
        remaining = total - consumed

        weeks_for_burn = min(data_points_count, 4)
        weights = [0.1, 0.2, 0.3, 0.4][:weeks_for_burn]
        weeks = get_last_n_weeks(weeks_for_burn)

        conn_context = (
            get_db_connection() if db_path is None else get_db_connection(db_path)
        )
        with conn_context as conn:
            cursor = conn.cursor()

            weekly_costs = []
            for week_info in weeks:
                wk_label = week_info[0]
                velocity = _get_velocity(profile_id, query_id, wk_label, 4, db_path)

                cursor.execute(
                    """
                    SELECT completed_items
                    FROM project_statistics
                    WHERE profile_id = ?
                      AND query_id = ?
                      AND week_label = ?
                """,
                    (profile_id, query_id, wk_label),
                )

                result = cursor.fetchone()
                completed = result[0] if result and result[0] else 0

                if velocity > 0:
                    cost_per_item = budget["team_cost_per_week_eur"] / velocity
                    weekly_cost = completed * cost_per_item
                else:
                    weekly_cost = 0.0

                weekly_costs.append(weekly_cost)
                logger.debug(
                    f"Week {wk_label}: completed={completed}, velocity={velocity:.2f}, "
                    f"cost={weekly_cost:.2f}"
                )

        if not weekly_costs or all(c == 0 for c in weekly_costs):
            return 0.0, 0.0

        weighted_burn_rate = sum(
            w * c for w, c in zip(weights, weekly_costs, strict=False)
        ) / sum(weights)

        if weighted_burn_rate > 0:
            runway_weeks = max(0, remaining / weighted_burn_rate)
        else:
            runway_weeks = float("inf")

        return runway_weeks, weighted_burn_rate

    except Exception as e:
        logger.error(f"Failed to calculate runway: {e}")
        return 0.0, 0.0


def calculate_weekly_cost_breakdowns(
    profile_id: str,
    query_id: str,
    week_label: str,
    data_points_count: int = 12,
    db_path: Path | None = None,
) -> tuple[list[dict[str, dict[str, float]]], list[str]]:

    try:
        budget = _get_current_budget(profile_id, query_id, db_path)
        if not budget:
            logger.info("[WEEKLY COST BREAKDOWN] No budget configured")
            return [], []

        velocity = _get_velocity(profile_id, query_id, week_label, 4, db_path)
        if velocity <= 0:
            logger.info("[WEEKLY COST BREAKDOWN] Velocity is zero")
            return [], []

        cost_per_item = budget["team_cost_per_week_eur"] / velocity

        weeks = get_last_n_weeks(data_points_count)
        week_labels = [w[0] for w in weeks]

        weekly_breakdowns = []

        for week in week_labels:
            week_snapshot = get_metric_snapshot(week, "flow_velocity")

            if week_snapshot:
                week_dist = week_snapshot.get("distribution", {})
                week_feature = week_dist.get("feature", 0)
                week_defect = week_dist.get("defect", 0)
                week_tech_debt = week_dist.get("tech_debt", 0)
                week_risk = week_dist.get("risk", 0)

                breakdown = {
                    "Feature": {
                        "cost": week_feature * cost_per_item,
                        "count": week_feature,
                    },
                    "Defect": {
                        "cost": week_defect * cost_per_item,
                        "count": week_defect,
                    },
                    "Technical Debt": {
                        "cost": week_tech_debt * cost_per_item,
                        "count": week_tech_debt,
                    },
                    "Risk": {
                        "cost": week_risk * cost_per_item,
                        "count": week_risk,
                    },
                }
            else:
                breakdown = {
                    "Feature": {"cost": 0.0, "count": 0},
                    "Defect": {"cost": 0.0, "count": 0},
                    "Technical Debt": {"cost": 0.0, "count": 0},
                    "Risk": {"cost": 0.0, "count": 0},
                }

            weekly_breakdowns.append(breakdown)

        logger.info(
            "[WEEKLY COST BREAKDOWN] Calculated "
            f"{len(weekly_breakdowns)} weekly breakdowns "
            f"for {data_points_count} weeks (cost_per_item={cost_per_item:.2f})"
        )

        return weekly_breakdowns, week_labels

    except Exception as e:
        logger.error(f"Failed to calculate weekly cost breakdowns: {e}", exc_info=True)
        return [], []


def _empty_breakdown() -> dict[str, dict[str, float]]:
    return {
        "Feature": {"cost": 0.0, "count": 0, "percentage": 0.0},
        "Defect": {"cost": 0.0, "count": 0, "percentage": 0.0},
        "Technical Debt": {"cost": 0.0, "count": 0, "percentage": 0.0},
        "Risk": {"cost": 0.0, "count": 0, "percentage": 0.0},
    }
