"""
State-of-the-art multi-dimensional project health calculator.

This module implements a comprehensive project health formula that uses ALL available
signals from across the application: Dashboard, DORA, Flow, Bug Analysis, Budget, and
Scope metrics. Each dimension is optional and automatically adjusts weights based on
data availability.

Formula - Comprehensive Multi-Dimensional:
- Delivery Performance (25%): velocity, throughput, completion rate
- Predictability (20%): velocity CV, forecast confidence, schedule adherence
- Quality (20%): bug density, DORA CFR, bug resolution, MTTR
- Efficiency (15%): flow efficiency, flow time, resource utilization
- Sustainability (10%): scope stability, WIP management, flow distribution
- Financial Health (10%): budget adherence, burn rate, runway

Each dimension uses multiple signals when available and automatically adjusts if data
is missing. The formula is context-aware (early vs late stage projects) and uses
appropriate normalization (sigmoid, logarithmic, linear).
"""

import math
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


def prepare_dashboard_metrics_for_health(
    completion_percentage: float = 0,
    current_velocity_items: float = 0,
    velocity_cv: float = 0,
    trend_direction: str = "stable",
    recent_velocity_change: float = 0,
    schedule_variance_days: float = 0,
    completion_confidence: float = 50,
) -> Dict[str, Any]:
    """Prepare dashboard metrics dictionary for comprehensive health calculation.

    This function ensures consistent metric formatting between the app dashboard
    and report generation (DRY principle).

    Args:
        completion_percentage: Project completion percentage (0-100)
        current_velocity_items: Current velocity in items per week
        velocity_cv: Coefficient of variation for velocity (percentage)
        trend_direction: Velocity trend ("improving", "stable", "declining")
        recent_velocity_change: Recent velocity change percentage
        schedule_variance_days: Days ahead/behind schedule (negative = ahead)
        completion_confidence: Forecast confidence percentage (0-100)

    Returns:
        Dictionary with standardized keys for health calculator
    """
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
    dashboard_metrics: Optional[Dict[str, Any]] = None,
    dora_metrics: Optional[Dict[str, Any]] = None,
    flow_metrics: Optional[Dict[str, Any]] = None,
    bug_metrics: Optional[Dict[str, Any]] = None,
    budget_metrics: Optional[Dict[str, Any]] = None,
    scope_metrics: Optional[Dict[str, Any]] = None,
    statistics_df: Optional[Any] = None,
) -> Dict[str, Any]:
    """Calculate comprehensive multi-dimensional project health score.

    Args:
        dashboard_metrics: Velocity, completion, remaining work, PERT forecasts
        dora_metrics: Deployment frequency, lead time, CFR, MTTR
        flow_metrics: Flow velocity, flow time, flow efficiency, flow load, distribution
        bug_metrics: Bug density, resolution rate, avg age, trend
        budget_metrics: Burn rate, runway, utilization, surplus
        scope_metrics: Scope change rate, stability index, throughput ratio
        statistics_df: Historical statistics DataFrame for calculations

    Returns:
        Dictionary with overall health score (0-100), dimension scores, and metadata
    """
    # Initialize dimension scores and weights
    dimensions: Dict[str, Dict[str, float]] = {
        "delivery": {"score": 0.0, "weight": 0.0, "max_weight": 25.0},
        "predictability": {"score": 0.0, "weight": 0.0, "max_weight": 20.0},
        "quality": {"score": 0.0, "weight": 0.0, "max_weight": 20.0},
        "efficiency": {"score": 0.0, "weight": 0.0, "max_weight": 15.0},
        "sustainability": {"score": 0.0, "weight": 0.0, "max_weight": 10.0},
        "financial": {"score": 0.0, "weight": 0.0, "max_weight": 10.0},
    }

    # Context: determine project maturity
    completion_pct = 0
    if dashboard_metrics:
        completion_pct = dashboard_metrics.get("completion_percentage", 0)

    project_stage = _determine_project_stage(completion_pct)

    logger.info(
        f"[HEALTH] Starting comprehensive calculation. "
        f"Completion: {completion_pct:.1f}%, Stage: {project_stage}"
    )

    # Calculate each dimension
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

    # Redistribute weights to always sum to 100% (dynamic weighting)
    total_weight = sum(d["weight"] for d in dimensions.values())

    if total_weight > 0 and abs(total_weight - 100) > 0.01:
        # When dimensions are missing, adjust max_weights proportionally
        # This allows remaining dimensions to reach 100% total while maintaining relative importance
        available_dims = [name for name, d in dimensions.items() if d["weight"] > 0]
        missing_weight = 100.0 - sum(
            dimensions[name]["max_weight"] for name in available_dims
        )

        if missing_weight > 0.01:
            # Redistribute missing weight proportionally to available dimensions' max_weights
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
                f"[HEALTH] Adjusted max_weights due to {len(dimensions) - len(available_dims)} missing dimensions"
            )

        # Now scale to 100% respecting adjusted caps
        capped_dims = []
        max_iterations = 10

        for iteration in range(max_iterations):
            current_total = sum(d["weight"] for d in dimensions.values())

            if abs(current_total - 100.0) < 0.01:
                break

            # Calculate how much we need to add/remove
            adjustment_needed = 100.0 - current_total

            # Find dimensions that can still accept weight
            adjustable_dims = [
                (name, dim)
                for name, dim in dimensions.items()
                if dim["weight"] > 0 and abs(dim["weight"] - dim["max_weight"]) > 0.01
            ]

            if not adjustable_dims:
                # All dimensions at their max, can't reach 100%
                break

            # Distribute adjustment proportionally to adjustable dimensions
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

    # Calculate weighted score: sum(score × weight/100)
    overall_score = sum(d["score"] * d["weight"] / 100 for d in dimensions.values())
    # Use round() instead of int() for consistency with display formatting (.0f rounds to nearest)
    overall_score = round(max(0, min(100, overall_score)))

    # Log results
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
    """Determine project maturity stage."""
    if completion_pct < 25:
        return "inception"
    elif completion_pct < 50:
        return "early"
    elif completion_pct < 75:
        return "mid"
    else:
        return "late"


def _calculate_delivery_dimension(
    dashboard_metrics: Optional[Dict],
    flow_metrics: Optional[Dict],
    statistics_df: Optional[Any],
) -> Tuple[float, float]:
    """Calculate Delivery Performance dimension (0-100 score, weight percentage).

    Signals:
    - Completion progress (30 points)
    - Velocity trend (35 points)
    - Throughput rate (35 points)
    """
    score = 0
    weight = 0
    max_points = 100

    # Signal 1: Completion Progress (30 points)
    if dashboard_metrics:
        completion_pct = dashboard_metrics.get("completion_percentage", 0)
        progress_score = (completion_pct / 100) * 30
        score += progress_score
        weight += 10  # 10% weight contribution
        logger.debug(f"[Delivery] Progress: {progress_score:.1f}/30 pts")

    # Signal 2: Velocity Trend (35 points)
    if dashboard_metrics:
        trend_direction = dashboard_metrics.get("trend_direction", "stable")
        recent_change = dashboard_metrics.get("recent_velocity_change", 0)

        if trend_direction == "improving" or recent_change > 10:
            trend_score = 35
        elif trend_direction == "stable" or abs(recent_change) <= 10:
            trend_score = 25
        else:  # declining
            trend_score = 10

        score += trend_score
        weight += 10  # 10% weight contribution
        logger.debug(f"[Delivery] Trend: {trend_score:.1f}/35 pts")

    # Signal 3: Throughput Rate (35 points)
    # Use Flow Velocity if available, fallback to dashboard velocity
    if flow_metrics and flow_metrics.get("has_data"):
        flow_velocity = flow_metrics.get("velocity", 0)
        # Sigmoid normalization: 5 items/week = 50%, 10+ items/week = 90%+
        throughput_factor = 1 / (1 + math.exp(-(flow_velocity - 5) / 2))
        throughput_score = throughput_factor * 35
        score += throughput_score
        weight += 5  # 5% weight contribution
        logger.info(
            f"[Delivery] Throughput (flow): velocity={flow_velocity:.2f}, factor={throughput_factor:.3f}, score={throughput_score:.1f}/35 pts"
        )
    elif dashboard_metrics:
        velocity_items = dashboard_metrics.get("current_velocity_items", 0)
        throughput_factor = 1 / (1 + math.exp(-(velocity_items - 3) / 1.5))
        throughput_score = throughput_factor * 35
        score += throughput_score
        weight += 5  # 5% weight contribution
        logger.info(
            f"[Delivery] Throughput (dash): velocity={velocity_items:.2f}, factor={throughput_factor:.3f}, score={throughput_score:.1f}/35 pts"
        )

    # Normalize to 0-100 scale
    if weight > 0:
        normalized_score = (score / max_points) * 100
    else:
        normalized_score = 50  # Neutral
        weight = 0

    return normalized_score, weight


def _calculate_predictability_dimension(
    dashboard_metrics: Optional[Dict],
    flow_metrics: Optional[Dict],
    statistics_df: Optional[Any],
) -> Tuple[float, float]:
    """Calculate Predictability dimension (0-100 score, weight percentage).

    Signals:
    - Velocity consistency/CV (50 points)
    - Schedule adherence (30 points)
    - Forecast confidence (20 points)
    """
    score = 0
    weight = 0
    max_points = 100

    # Signal 1: Velocity Consistency (50 points)
    if dashboard_metrics:
        velocity_cv = dashboard_metrics.get("velocity_cv", 0)
        # Gentler sigmoid: 70 midpoint, 20 divisor, 3pt floor
        consistency_factor = 1 / (1 + math.exp((velocity_cv - 70) / 20))
        consistency_score = (consistency_factor * 47) + 3  # 3-50 point range
        score += consistency_score
        weight += 12  # 12% weight contribution
        logger.debug(
            f"[Predictability] Consistency (CV={velocity_cv:.1f}%): {consistency_score:.1f}/50 pts"
        )

    # Signal 2: Schedule Adherence (30 points)
    if dashboard_metrics:
        schedule_variance = dashboard_metrics.get("schedule_variance_days", 0)
        buffer_days = (
            schedule_variance  # Positive = ahead (no negation - already correct sign)
        )
        schedule_factor = (math.tanh(buffer_days / 20) + 1) / 2  # 0-1
        schedule_score = schedule_factor * 30
        score += schedule_score
        weight += 5  # 5% weight contribution
        logger.debug(f"[Predictability] Schedule: {schedule_score:.1f}/30 pts")

    # Signal 3: Forecast Confidence (20 points)
    if dashboard_metrics:
        confidence = dashboard_metrics.get("completion_confidence", 50)
        confidence_score = (confidence / 100) * 20
        score += confidence_score
        weight += 3  # 3% weight contribution
        logger.debug(f"[Predictability] Confidence: {confidence_score:.1f}/20 pts")

    # Normalize to 0-100
    if weight > 0:
        normalized_score = (score / max_points) * 100
    else:
        normalized_score = 50
        weight = 0

    return normalized_score, weight


def _calculate_quality_dimension(
    bug_metrics: Optional[Dict],
    dora_metrics: Optional[Dict],
    project_stage: str,
) -> Tuple[float, float]:
    """Calculate Quality dimension (0-100 score, weight percentage).

    Signals:
    - Bug resolution rate (30 points)
    - Change failure rate (25 points)
    - MTTR (20 points)
    - Bug density/age (25 points)
    """
    score = 0
    weight = 0
    max_points = 100

    # Signal 1: Bug Resolution Rate (30 points)
    if bug_metrics and bug_metrics.get("has_data"):
        resolution_rate = bug_metrics.get("resolution_rate", 0)
        # Linear: 70% = 21pts, 85% = 25.5pts, 100% = 30pts
        # resolution_rate is already a percentage (0-100), so divide by 100 to get 0-1
        resolution_score = (resolution_rate / 100) * 30
        score += resolution_score
        weight += 8  # 8% weight contribution
        logger.info(
            f"[Quality] Bug Resolution: rate={resolution_rate:.2f}%, score={resolution_score:.1f}/30 pts"
        )
    else:
        logger.info(
            f"[Quality] Bug Resolution: SKIPPED (bug_metrics={'available' if bug_metrics else 'None'}, has_data={bug_metrics.get('has_data') if bug_metrics else 'N/A'})"
        )

    # Signal 2: Change Failure Rate (25 points)
    if dora_metrics and dora_metrics.get("has_data"):
        cfr = dora_metrics.get("change_failure_rate", 0)
        # Inverted: 0% CFR = 25pts, 15% = 12.5pts, 30%+ = 0pts
        cfr_score = max(0, 25 * (1 - min(cfr / 30, 1)))
        score += cfr_score
        weight += 6  # 6% weight contribution
        logger.info(f"[Quality] CFR: rate={cfr:.2f}%, score={cfr_score:.1f}/25 pts")
    else:
        logger.info(
            f"[Quality] CFR: SKIPPED (dora_metrics={'available' if dora_metrics else 'None'}, has_data={dora_metrics.get('has_data') if dora_metrics else 'N/A'})"
        )

    # Signal 3: MTTR (20 points)
    if dora_metrics and dora_metrics.get("has_data"):
        mttr_hours = dora_metrics.get("mttr_hours", 0)
        if mttr_hours:
            # Logarithmic: <1hr = 20pts, 24hr = 10pts, 168hr(1wk) = 0pts
            if mttr_hours < 1:
                mttr_score = 20
            elif mttr_hours < 168:
                mttr_score = 20 * (1 - math.log10(mttr_hours / 1) / math.log10(168))
            else:
                mttr_score = 0
            score += mttr_score
            weight += 3  # 3% weight contribution
            logger.info(
                f"[Quality] MTTR: hours={mttr_hours:.1f}, score={mttr_score:.1f}/20 pts"
            )
        else:
            logger.info("[Quality] MTTR: SKIPPED (mttr_hours=0 or None)")
    else:
        logger.info(
            f"[Quality] MTTR: SKIPPED (dora_metrics={'available' if dora_metrics else 'None'})"
        )

    # Signal 4: Bug Density/Age (25 points)
    if bug_metrics and bug_metrics.get("has_data"):
        # Sub-signal 4a: Bug density (capacity consumed)
        capacity_consumed = bug_metrics.get("capacity_consumed_by_bugs", 0)
        # Inverted: 0% = 15pts, 20% = 7.5pts, 40%+ = 0pts
        density_score = max(0, 15 * (1 - min(capacity_consumed / 0.4, 1)))

        # Sub-signal 4b: Average bug age (age of OPEN bugs, not resolution time of closed bugs)
        avg_age = bug_metrics.get("avg_age_days", 0)

        # Logarithmic: <3days = 10pts, 7days = 7pts, 30days+ = 0pts
        if avg_age < 3:
            age_score = 10
        elif avg_age < 30:
            age_score = 10 * (1 - math.log10(avg_age / 3) / math.log10(10))
        else:
            age_score = 0

        bug_health_score = density_score + age_score
        score += bug_health_score
        weight += 3  # 3% weight contribution
        logger.info(
            f"[Quality] Bug Health: capacity={capacity_consumed:.2f}, avg_age={avg_age:.1f}d, density_score={density_score:.1f}, age_score={age_score:.1f}, total={bug_health_score:.1f}/25 pts"
        )
    else:
        logger.info(
            f"[Quality] Bug Health: SKIPPED (bug_metrics={'available' if bug_metrics else 'None'})"
        )

    # Normalize to 0-100
    if weight > 0:
        normalized_score = (score / max_points) * 100
    else:
        normalized_score = 50
        weight = 0

    return normalized_score, weight


def _calculate_efficiency_dimension(
    flow_metrics: Optional[Dict],
    dashboard_metrics: Optional[Dict],
) -> Tuple[float, float]:
    """Calculate Efficiency dimension (0-100 score, weight percentage).

    Signals:
    - Flow efficiency (40 points)
    - Flow time (35 points)
    - Lead time for changes (25 points)
    """
    score = 0
    weight = 0
    max_points = 100

    # Signal 1: Flow Efficiency (40 points)
    if flow_metrics and flow_metrics.get("has_data"):
        efficiency_pct = flow_metrics.get("efficiency", 0)
        # Linear: 25% = 25pts, 35% = 35pts, 50%+ = 40pts
        efficiency_score = min(40, (efficiency_pct / 50) * 40)
        score += efficiency_score
        weight += 7  # 7% weight contribution
        logger.debug(f"[Efficiency] Flow Efficiency: {efficiency_score:.1f}/40 pts")

    # Signal 2: Flow Time (35 points)
    if flow_metrics and flow_metrics.get("has_data"):
        flow_time_days = flow_metrics.get("flow_time", 0)
        # Inverted sigmoid: 3days = 28pts, 7days = 17.5pts, 21days+ = 0pts
        if flow_time_days > 0:
            time_factor = 1 / (1 + math.exp((flow_time_days - 7) / 5))
            flow_time_score = time_factor * 35
            score += flow_time_score
            weight += 5  # 5% weight contribution
            logger.debug(f"[Efficiency] Flow Time: {flow_time_score:.1f}/35 pts")

    # Signal 3: Lead Time for Changes (25 points) - from DORA if available
    # (Would need dora_metrics passed in - skipping for now, can add later)

    # Normalize to 0-100
    if weight > 0:
        normalized_score = (score / max_points) * 100
    else:
        normalized_score = 50
        weight = 0

    return normalized_score, weight


def _calculate_sustainability_dimension(
    scope_metrics: Optional[Dict],
    flow_metrics: Optional[Dict],
    project_stage: str,
) -> Tuple[float, float]:
    """Calculate Sustainability dimension (0-100 score, weight percentage).

    Signals:
    - Scope stability (40 points) - context-aware
    - WIP management (35 points)
    - Flow distribution balance (25 points)
    """
    score = 0
    weight = 0
    max_points = 100

    # Context factor for scope penalties
    context_factor = 1.0
    if project_stage == "inception":
        context_factor = 0.2  # Very light penalties
    elif project_stage == "early":
        context_factor = 0.3  # Light penalties
    elif project_stage == "mid":
        context_factor = 0.6  # Moderate penalties
    # late = 1.0 (full penalties)

    # Signal 1: Scope Stability (40 points) - CONTEXT-AWARE
    if scope_metrics:
        scope_change_rate = scope_metrics.get("scope_change_rate", 0)

        # Logarithmic penalty with context adjustment
        if scope_change_rate <= 100:
            scope_penalty = (scope_change_rate / 100) * 12 * context_factor
        else:
            scope_penalty = (
                12 + math.log10(scope_change_rate / 100) * 28
            ) * context_factor

        scope_score = max(0, 40 - scope_penalty)
        score += scope_score
        weight += 6  # 6% weight contribution
        logger.info(
            f"[Sustainability] Scope (context={context_factor}, change_rate={scope_change_rate:.1f}%): {scope_score:.1f}/40 pts"
        )

    # Signal 2: WIP Management (35 points)
    if flow_metrics and flow_metrics.get("has_data"):
        wip = flow_metrics.get("wip", 0)
        velocity = flow_metrics.get("velocity", 1)

        # Ideal WIP = 1.5 × velocity (Little's Law with buffer)
        ideal_wip = velocity * 1.5
        wip_ratio = wip / ideal_wip if ideal_wip > 0 else 1

        # Bell curve: 0.8-1.2× ideal = full points, >2× or <0.5× = 0pts
        if 0.8 <= wip_ratio <= 1.2:
            wip_score = 35
        elif wip_ratio < 0.8:
            # Underutilized
            wip_score = 35 * (wip_ratio / 0.8)
        else:
            # Overloaded
            wip_score = max(0, 35 * (1 - (wip_ratio - 1.2) / 1.3))

        score += wip_score
        weight += 3  # 3% weight contribution
        logger.info(
            f"[Sustainability] WIP (wip={wip}, velocity={velocity:.2f}, ratio={wip_ratio:.2f}): {wip_score:.1f}/35 pts"
        )

    # Signal 3: Flow Distribution Balance (25 points)
    if flow_metrics and flow_metrics.get("has_data"):
        distribution = flow_metrics.get("work_distribution", {})
        total = distribution.get("total", 0)

        if total > 0:
            feature_pct = (distribution.get("feature", 0) / total) * 100
            defect_pct = (distribution.get("defect", 0) / total) * 100
            tech_debt_pct = (distribution.get("tech_debt", 0) / total) * 100

            # Ideal: 50-70% features, 10-30% defects, 10-20% tech debt
            feature_score = 10 * (1 - abs(feature_pct - 60) / 60)  # 10pts
            defect_score = 8 * (1 - abs(defect_pct - 20) / 50)  # 8pts
            tech_debt_score = 7 * (1 - abs(tech_debt_pct - 15) / 50)  # 7pts

            distribution_score = max(0, feature_score + defect_score + tech_debt_score)
            score += distribution_score
            weight += 1  # 1% weight contribution
            logger.info(
                f"[Sustainability] Distribution (feature={feature_pct:.0f}%, defect={defect_pct:.0f}%, tech_debt={tech_debt_pct:.0f}%): {distribution_score:.1f}/25 pts"
            )

    # Normalize to 0-100
    if weight > 0:
        normalized_score = (score / max_points) * 100
    else:
        normalized_score = 50
        weight = 0

    return normalized_score, weight


def _calculate_financial_dimension(
    budget_metrics: Optional[Dict],
) -> Tuple[float, float]:
    """Calculate Financial Health dimension (0-100 score, weight percentage).

    Signals:
    - Budget adherence (40 points)
    - Runway adequacy (35 points)
    - Burn rate health (25 points)
    """
    score = 0
    weight = 0
    max_points = 100

    if not budget_metrics or not budget_metrics.get("has_data"):
        return 50, 0  # Neutral, no weight

    # Signal 1: Budget Adherence (40 points)
    burn_rate_variance = budget_metrics.get("burn_rate_variance_pct", 0)
    # ±10% = good (32pts), ±25% = moderate (20pts), >50% = poor (0pts)
    abs_variance = abs(burn_rate_variance)
    if abs_variance < 10:
        budget_score = 40 - (abs_variance / 10) * 8  # 32-40 pts
    elif abs_variance < 50:
        budget_score = 32 * (1 - (abs_variance - 10) / 40)  # 0-32 pts
    else:
        budget_score = 0
    score += budget_score
    weight += 5  # 5% weight contribution
    logger.debug(f"[Financial] Budget Adherence: {budget_score:.1f}/40 pts")

    # Signal 2: Runway Adequacy (35 points)
    runway_vs_baseline = budget_metrics.get("runway_vs_baseline_pct", 0)
    # >10% ahead = 35pts, on track = 20pts, <-25% behind = 0pts
    if runway_vs_baseline > 0:
        runway_score = min(35, 20 + (runway_vs_baseline / 10) * 15)
    else:
        runway_score = max(0, 20 + (runway_vs_baseline / 25) * 20)
    score += runway_score
    weight += 3  # 3% weight contribution
    logger.debug(f"[Financial] Runway: {runway_score:.1f}/35 pts")

    # Signal 3: Burn Rate Health (25 points)
    utilization_vs_pace = budget_metrics.get("utilization_vs_pace_pct", 0)
    # ±10% of pace = 25pts, ±25% = 12.5pts, >50% = 0pts
    abs_util_variance = abs(utilization_vs_pace)
    if abs_util_variance < 10:
        burn_score = 25 - (abs_util_variance / 10) * 5  # 20-25 pts
    elif abs_util_variance < 50:
        burn_score = 20 * (1 - (abs_util_variance - 10) / 40)  # 0-20 pts
    else:
        burn_score = 0
    score += burn_score
    weight += 2  # 2% weight contribution
    logger.debug(f"[Financial] Burn Rate: {burn_score:.1f}/25 pts")

    # Normalize to 0-100
    normalized_score = (score / max_points) * 100

    return normalized_score, weight
