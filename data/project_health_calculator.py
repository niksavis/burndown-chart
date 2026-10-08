import logging
import math
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


def prepare_dashboard_metrics_for_health(
    completion_percentage: float = 0,
    current_velocity_items: float = 0,
    velocity_cv: float = 0,
    trend_direction: str = "stable",
    recent_velocity_change: float = 0,
    schedule_variance_days: float = 0,
    completion_confidence: float = 50,
) -> dict[str, Any]:

    return {
        "completion_percentage": completion_percentage,
        "current_velocity_items": current_velocity_items,
        "velocity_cv": velocity_cv,
        "trend_direction": trend_direction,
        "recent_velocity_change": recent_velocity_change,
        "schedule_variance_days": schedule_variance_days,
        "completion_confidence": completion_confidence,
    }


def calculate_comprehensive_project_health(
    dashboard_metrics: dict[str, Any] | None = None,
    dora_metrics: dict[str, Any] | None = None,
    flow_metrics: dict[str, Any] | None = None,
    bug_metrics: dict[str, Any] | None = None,
    budget_metrics: dict[str, Any] | None = None,
    scope_metrics: dict[str, Any] | None = None,
    statistics_df: Any | None = None,
) -> dict[str, Any]:

    dimensions: dict[str, dict[str, float]] = {
        "delivery": {"score": 0.0, "weight": 0.0, "max_weight": 25.0},
        "predictability": {"score": 0.0, "weight": 0.0, "max_weight": 20.0},
        "quality": {"score": 0.0, "weight": 0.0, "max_weight": 20.0},
        "efficiency": {"score": 0.0, "weight": 0.0, "max_weight": 15.0},
        "sustainability": {"score": 0.0, "weight": 0.0, "max_weight": 10.0},
        "financial": {"score": 0.0, "weight": 0.0, "max_weight": 10.0},
    }

    completion_pct = 0
    if dashboard_metrics:
        completion_pct = dashboard_metrics.get("completion_percentage", 0)

    project_stage = _determine_project_stage(completion_pct)

    logger.info(
        f"[HEALTH] Starting comprehensive calculation. "
        f"Completion: {completion_pct:.1f}%, Stage: {project_stage}"
    )

    delivery_score, delivery_weight = _calculate_delivery_dimension(
        dashboard_metrics, flow_metrics, statistics_df
    )
    dimensions["delivery"]["score"] = delivery_score
    dimensions["delivery"]["weight"] = delivery_weight

    predictability_score, predictability_weight = _calculate_predictability_dimension(
        dashboard_metrics, flow_metrics, statistics_df
    )
    dimensions["predictability"]["score"] = predictability_score
    dimensions["predictability"]["weight"] = predictability_weight

    quality_score, quality_weight = _calculate_quality_dimension(
        bug_metrics, dora_metrics, project_stage
    )
    dimensions["quality"]["score"] = quality_score
    dimensions["quality"]["weight"] = quality_weight

    efficiency_score, efficiency_weight = _calculate_efficiency_dimension(
        flow_metrics, dashboard_metrics
    )
    dimensions["efficiency"]["score"] = efficiency_score
    dimensions["efficiency"]["weight"] = efficiency_weight

    sustainability_score, sustainability_weight = _calculate_sustainability_dimension(
        scope_metrics, flow_metrics, project_stage
    )
    dimensions["sustainability"]["score"] = sustainability_score
    dimensions["sustainability"]["weight"] = sustainability_weight

    financial_score, financial_weight = _calculate_financial_dimension(budget_metrics)
    dimensions["financial"]["score"] = financial_score
    dimensions["financial"]["weight"] = financial_weight

    total_weight = sum(d["weight"] for d in dimensions.values())

    if total_weight > 0 and abs(total_weight - 100) > 0.01:
        available_dims = [name for name, d in dimensions.items() if d["weight"] > 0]
        missing_weight = 100.0 - sum(
            dimensions[name]["max_weight"] for name in available_dims
        )

        if missing_weight > 0.01:
            available_max_total = sum(
                dimensions[name]["max_weight"] for name in available_dims
            )
            for name in available_dims:
                original_max = dimensions[name]["max_weight"]
                proportion = original_max / available_max_total
                dimensions[name]["max_weight"] = original_max + (
                    missing_weight * proportion
                )
            logger.debug(
                "[HEALTH] Adjusted max_weights due to "
                f"{len(dimensions) - len(available_dims)} missing dimensions"
            )

        capped_dims = []
        max_iterations = 10

        for _iteration in range(max_iterations):
            current_total = sum(d["weight"] for d in dimensions.values())

            if abs(current_total - 100.0) < 0.01:
                break

            adjustment_needed = 100.0 - current_total

            adjustable_dims = [
                (name, dim)
                for name, dim in dimensions.items()
                if dim["weight"] > 0 and abs(dim["weight"] - dim["max_weight"]) > 0.01
            ]

            if not adjustable_dims:
                break

            adjustable_total = sum(dim["weight"] for name, dim in adjustable_dims)

            for dim_name, dim in adjustable_dims:
                if adjustable_total > 0:
                    proportion = dim["weight"] / adjustable_total
                    adjustment = adjustment_needed * proportion
                    new_weight = min(
                        dim["max_weight"], max(0, dim["weight"] + adjustment)
                    )
                    dimensions[dim_name]["weight"] = new_weight

                    if abs(new_weight - dim["max_weight"]) < 0.01:
                        if dim_name not in capped_dims:
                            capped_dims.append(dim_name)

        final_total = sum(d["weight"] for d in dimensions.values())
        logger.debug(
            f"[HEALTH] Weight redistribution: {total_weight:.1f}% → {final_total:.1f}% "
            f"(capped: {', '.join(capped_dims) if capped_dims else 'none'})"
        )

    overall_score = sum(d["score"] * d["weight"] / 100 for d in dimensions.values())
    overall_score = round(max(0, min(100, overall_score)))

    logger.info(
        f"[HEALTH] Overall Score: {overall_score}/100 "
        f"(Delivery:{delivery_score:.1f}×{delivery_weight:.0f}%, "
        f"Predict:{predictability_score:.1f}×{predictability_weight:.0f}%, "
        f"Quality:{quality_score:.1f}×{quality_weight:.0f}%, "
        f"Efficiency:{efficiency_score:.1f}×{efficiency_weight:.0f}%, "
        f"Sustain:{sustainability_score:.1f}×{sustainability_weight:.0f}%, "
        f"Financial:{financial_score:.1f}×{financial_weight:.0f}%)"
    )

    return {
        "overall_score": overall_score,
        "dimensions": dimensions,
        "project_stage": project_stage,
        "completion_percentage": completion_pct,
        "formula_version": "3.0",
        "timestamp": datetime.now().isoformat(),
    }


def _determine_project_stage(completion_pct: float) -> str:
    if completion_pct < 25:
        return "inception"
    elif completion_pct < 50:
        return "early"
    elif completion_pct < 75:
        return "mid"
    else:
        return "late"


def _calculate_delivery_dimension(
    dashboard_metrics: dict | None,
    flow_metrics: dict | None,
    statistics_df: Any | None,
) -> tuple[float, float]:

    score = 0
    weight = 0
    max_points = 100

    if dashboard_metrics:
        completion_pct = dashboard_metrics.get("completion_percentage", 0)
        progress_score = (completion_pct / 100) * 30
        score += progress_score
        weight += 10
        logger.info(
            f"[Delivery] Progress: completion={completion_pct:.2f}%, "
            f"score={progress_score:.1f}/30 pts"
        )

    if dashboard_metrics:
        trend_direction = dashboard_metrics.get("trend_direction", "stable")
        recent_change = dashboard_metrics.get("recent_velocity_change", 0)

        if trend_direction == "improving" or recent_change > 10:
            trend_score = 35
        elif trend_direction == "stable" or abs(recent_change) <= 10:
            trend_score = 25
        else:
            trend_score = 10

        score += trend_score
        weight += 10
        logger.info(
            f"[Delivery] Trend: direction={trend_direction}, "
            f"change={recent_change:.1f}%, score={trend_score:.1f}/35 pts"
        )

    if flow_metrics and flow_metrics.get("has_data"):
        flow_velocity = flow_metrics.get("velocity", 0)
        throughput_factor = 1 / (1 + math.exp(-(flow_velocity - 5) / 2))
        throughput_score = throughput_factor * 35
        score += throughput_score
        weight += 5
        logger.info(
            f"[Delivery] Throughput (flow): velocity={flow_velocity:.2f}, "
            f"factor={throughput_factor:.3f}, "
            f"score={throughput_score:.1f}/35 pts"
        )
    elif dashboard_metrics:
        velocity_items = dashboard_metrics.get("current_velocity_items", 0)
        throughput_factor = 1 / (1 + math.exp(-(velocity_items - 3) / 1.5))
        throughput_score = throughput_factor * 35
        score += throughput_score
        weight += 5
        logger.info(
            f"[Delivery] Throughput (dash): velocity={velocity_items:.2f}, "
            f"factor={throughput_factor:.3f}, "
            f"score={throughput_score:.1f}/35 pts"
        )

    if weight > 0:
        normalized_score = (score / max_points) * 100
    else:
        normalized_score = 50
        weight = 0

    logger.info(
        f"[Delivery] TOTAL: raw_score={score:.1f}/{max_points}, "
        f"normalized={normalized_score:.1f}/100, weight={weight}%"
    )
    return normalized_score, weight


def _calculate_predictability_dimension(
    dashboard_metrics: dict | None,
    flow_metrics: dict | None,
    statistics_df: Any | None,
) -> tuple[float, float]:

    score = 0
    weight = 0
    max_points = 100

    if dashboard_metrics:
        velocity_cv = dashboard_metrics.get("velocity_cv", 0)
        consistency_factor = 1 / (1 + math.exp((velocity_cv - 70) / 20))
        consistency_score = (consistency_factor * 47) + 3
        score += consistency_score
        weight += 12
        logger.debug(
            f"[Predictability] Consistency (CV={velocity_cv:.1f}%): "
            f"{consistency_score:.1f}/50 pts"
        )

    if dashboard_metrics:
        schedule_variance = dashboard_metrics.get("schedule_variance_days", 0)
        buffer_days = schedule_variance
        schedule_factor = (math.tanh(buffer_days / 20) + 1) / 2
        schedule_score = schedule_factor * 30
        score += schedule_score
        weight += 5
        logger.debug(f"[Predictability] Schedule: {schedule_score:.1f}/30 pts")

    if dashboard_metrics:
        confidence = dashboard_metrics.get("completion_confidence", 50)
        confidence_score = (confidence / 100) * 20
        score += confidence_score
        weight += 3
        logger.debug(f"[Predictability] Confidence: {confidence_score:.1f}/20 pts")

    if weight > 0:
        normalized_score = (score / max_points) * 100
    else:
        normalized_score = 50
        weight = 0

    return normalized_score, weight


def _calculate_quality_dimension(
    bug_metrics: dict | None,
    dora_metrics: dict | None,
    project_stage: str,
) -> tuple[float, float]:

    score = 0
    weight = 0
    max_points = 100

    if bug_metrics and bug_metrics.get("has_data"):
        resolution_rate = bug_metrics.get("resolution_rate", 0)
        resolution_score = (resolution_rate / 100) * 30
        score += resolution_score
        weight += 8
        logger.info(
            f"[Quality] Bug Resolution: rate={resolution_rate:.2f}%, "
            f"score={resolution_score:.1f}/30 pts"
        )
    else:
        logger.info(
            "[Quality] Bug Resolution: SKIPPED "
            f"(bug_metrics={'available' if bug_metrics else 'None'}, "
            f"has_data={bug_metrics.get('has_data') if bug_metrics else 'N/A'})"
        )

    if dora_metrics and dora_metrics.get("has_data"):
        cfr = dora_metrics.get("change_failure_rate", 0)
        cfr_score = max(0, 25 * (1 - min(cfr / 30, 1)))
        score += cfr_score
        weight += 6
        logger.info(f"[Quality] CFR: rate={cfr:.2f}%, score={cfr_score:.1f}/25 pts")
    else:
        logger.info(
            "[Quality] CFR: SKIPPED "
            f"(dora_metrics={'available' if dora_metrics else 'None'}, "
            f"has_data={dora_metrics.get('has_data') if dora_metrics else 'N/A'})"
        )

    if dora_metrics and dora_metrics.get("has_data"):
        mttr_hours = dora_metrics.get("mttr_hours", 0)
        if mttr_hours:
            if mttr_hours < 1:
                mttr_score = 20
            elif mttr_hours < 168:
                mttr_score = 20 * (1 - math.log10(mttr_hours / 1) / math.log10(168))
            else:
                mttr_score = 0
            score += mttr_score
            weight += 3
            logger.info(
                f"[Quality] MTTR: hours={mttr_hours:.1f}, score={mttr_score:.1f}/20 pts"
            )
        else:
            logger.info("[Quality] MTTR: SKIPPED (mttr_hours=0 or None)")
    else:
        logger.info(
            "[Quality] MTTR: SKIPPED "
            f"(dora_metrics={'available' if dora_metrics else 'None'})"
        )

    if bug_metrics and bug_metrics.get("has_data"):
        capacity_consumed = bug_metrics.get("capacity_consumed_by_bugs", 0)
        density_score = max(0, 15 * (1 - min(capacity_consumed / 0.4, 1)))

        avg_age = bug_metrics.get("avg_age_days", 0)

        if avg_age < 3:
            age_score = 10
        elif avg_age < 30:
            age_score = 10 * (1 - math.log10(avg_age / 3) / math.log10(10))
        else:
            age_score = 0

        bug_health_score = density_score + age_score
        score += bug_health_score
        weight += 3
        logger.info(
            f"[Quality] Bug Health: capacity={capacity_consumed:.2f}, "
            f"avg_age={avg_age:.1f}d, density_score={density_score:.1f}, "
            f"age_score={age_score:.1f}, total={bug_health_score:.1f}/25 pts"
        )
    else:
        logger.info(
            "[Quality] Bug Health: SKIPPED "
            f"(bug_metrics={'available' if bug_metrics else 'None'})"
        )

    if weight > 0:
        normalized_score = (score / max_points) * 100
    else:
        normalized_score = 50
        weight = 0

    return normalized_score, weight


def _calculate_efficiency_dimension(
    flow_metrics: dict | None,
    dashboard_metrics: dict | None,
) -> tuple[float, float]:

    score = 0
    weight = 0
    max_points = 100

    if flow_metrics and flow_metrics.get("has_data"):
        efficiency_pct = flow_metrics.get("efficiency", 0)
        efficiency_score = min(40, (efficiency_pct / 50) * 40)
        score += efficiency_score
        weight += 7
        logger.debug(f"[Efficiency] Flow Efficiency: {efficiency_score:.1f}/40 pts")

    if flow_metrics and flow_metrics.get("has_data"):
        flow_time_days = flow_metrics.get("flow_time", 0)
        if flow_time_days > 0:
            time_factor = 1 / (1 + math.exp((flow_time_days - 7) / 5))
            flow_time_score = time_factor * 35
            score += flow_time_score
            weight += 5
            logger.debug(f"[Efficiency] Flow Time: {flow_time_score:.1f}/35 pts")

    if weight > 0:
        normalized_score = (score / max_points) * 100
    else:
        normalized_score = 50
        weight = 0

    return normalized_score, weight


def _calculate_sustainability_dimension(
    scope_metrics: dict | None,
    flow_metrics: dict | None,
    project_stage: str,
) -> tuple[float, float]:

    score = 0
    weight = 0
    max_points = 100

    context_factor = 1.0
    if project_stage == "inception":
        context_factor = 0.2
    elif project_stage == "early":
        context_factor = 0.3
    elif project_stage == "mid":
        context_factor = 0.6

    if scope_metrics:
        scope_change_rate = scope_metrics.get("scope_change_rate", 0)

        if scope_change_rate <= 100:
            scope_penalty = (scope_change_rate / 100) * 12 * context_factor
        else:
            scope_penalty = (
                12 + math.log10(scope_change_rate / 100) * 28
            ) * context_factor

        scope_score = max(0, 40 - scope_penalty)
        score += scope_score
        weight += 6
        logger.info(
            f"[Sustainability] Scope (context={context_factor}, "
            f"change_rate={scope_change_rate:.1f}%): {scope_score:.1f}/40 pts"
        )

    if flow_metrics and flow_metrics.get("has_data"):
        wip = flow_metrics.get("wip", 0)
        velocity = flow_metrics.get("velocity", 1)

        ideal_wip = velocity * 1.5
        wip_ratio = wip / ideal_wip if ideal_wip > 0 else 1

        if 0.8 <= wip_ratio <= 1.2:
            wip_score = 35
        elif wip_ratio < 0.8:
            wip_score = 35 * (wip_ratio / 0.8)
        else:
            wip_score = max(0, 35 * (1 - (wip_ratio - 1.2) / 1.3))

        score += wip_score
        weight += 3
        logger.info(
            f"[Sustainability] WIP (wip={wip}, velocity={velocity:.2f}, "
            f"ratio={wip_ratio:.2f}): {wip_score:.1f}/35 pts"
        )

    if flow_metrics and flow_metrics.get("has_data"):
        distribution = flow_metrics.get("work_distribution", {})
        total = distribution.get("total", 0)

        if total > 0:
            feature_pct = (distribution.get("feature", 0) / total) * 100
            defect_pct = (distribution.get("defect", 0) / total) * 100
            tech_debt_pct = (distribution.get("tech_debt", 0) / total) * 100

            feature_score = 10 * (1 - abs(feature_pct - 60) / 60)
            defect_score = 8 * (1 - abs(defect_pct - 20) / 50)
            tech_debt_score = 7 * (1 - abs(tech_debt_pct - 15) / 50)

            distribution_score = max(0, feature_score + defect_score + tech_debt_score)
            score += distribution_score
            weight += 1
            logger.info(
                f"[Sustainability] Distribution "
                f"(feature={feature_pct:.0f}%, defect={defect_pct:.0f}%, "
                f"tech_debt={tech_debt_pct:.0f}%): "
                f"{distribution_score:.1f}/25 pts"
            )

    if weight > 0:
        normalized_score = (score / max_points) * 100
    else:
        normalized_score = 50
        weight = 0

    return normalized_score, weight


def _calculate_financial_dimension(
    budget_metrics: dict | None,
) -> tuple[float, float]:

    score = 0
    weight = 0
    max_points = 100

    if not budget_metrics or not budget_metrics.get("has_data"):
        return 50, 0

    burn_rate_variance = budget_metrics.get("burn_rate_variance_pct", 0)
    abs_variance = abs(burn_rate_variance)
    if abs_variance < 10:
        budget_score = 40 - (abs_variance / 10) * 8
    elif abs_variance < 50:
        budget_score = 32 * (1 - (abs_variance - 10) / 40)
    else:
        budget_score = 0
    score += budget_score
    weight += 5
    logger.debug(f"[Financial] Budget Adherence: {budget_score:.1f}/40 pts")

    runway_vs_baseline = budget_metrics.get("runway_vs_baseline_pct", 0)
    if runway_vs_baseline > 0:
        runway_score = min(35, 20 + (runway_vs_baseline / 10) * 15)
    else:
        runway_score = max(0, 20 + (runway_vs_baseline / 25) * 20)
    score += runway_score
    weight += 3
    logger.debug(f"[Financial] Runway: {runway_score:.1f}/35 pts")

    utilization_vs_pace = budget_metrics.get("utilization_vs_pace_pct", 0)
    abs_util_variance = abs(utilization_vs_pace)
    if abs_util_variance < 10:
        burn_score = 25 - (abs_util_variance / 10) * 5
    elif abs_util_variance < 50:
        burn_score = 20 * (1 - (abs_util_variance - 10) / 40)
    else:
        burn_score = 0
    score += burn_score
    weight += 2
    logger.debug(f"[Financial] Burn Rate: {burn_score:.1f}/25 pts")

    normalized_score = (score / max_points) * 100

    return normalized_score, weight
